from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, send_file, flash
)
import os
import uuid
import json

# App config
import config

# Core modules
from core.storage import Storage
from core.agent import Agent
from core.extensions import db, login_manager
from core.models import User, AnalysisLog
import pandas as pd
from flask_login import login_user, login_required, logout_user, current_user


# -------------------------------------------------
# APP INITIALIZATION
# -------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{config.DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Init Extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

storage = Storage()


# -------------------------------------------------
# ROUTE 1: LANDING PAGE
# -------------------------------------------------
@app.route("/")
def get_started():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    return render_template("get_started.html")

# -------------------------------------------------
# AUTH ROUTES
# -------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("upload"))
        flash("Invalid username or password")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("register"))
            
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for("upload"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# -------------------------------------------------
# ROUTE 2: UPLOAD PAGE
# -------------------------------------------------
@app.route("/upload")
@login_required
def upload():
    return render_template("upload.html")


# -------------------------------------------------
# ROUTE 3: HANDLE FILE UPLOAD (API)
# -------------------------------------------------
@app.route("/upload_file", methods=["POST"])
@login_required
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not storage.allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Only CSV and Excel files are allowed"
            }), 400

        session_id = str(uuid.uuid4())
        filepath, filename = storage.save_upload(file, session_id)

        if not filepath:
            return jsonify({"success": False, "error": "File save failed"}), 500

        session["session_id"] = session_id

        return jsonify({
            "success": True,
            "filename": filename,
            "redirect": url_for("overview")
        })

    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------
# ROUTE 4: OVERVIEW PAGE
# -------------------------------------------------
@app.route("/overview") 
@login_required
def overview():
    session_id = session.get("session_id")
    if not session_id:
        return redirect(url_for("upload"))

    session_info = storage.get_session(session_id)
    if not session_info:
        return redirect(url_for("upload"))

    df = storage.load_dataframe(session_info["filepath"])
    if df is None:
        return redirect(url_for("upload"))

    preview = {
        "columns": list(df.columns),
        "rows": df.head(config.PREVIEW_ROWS).to_dict("records"),
        "total_rows": len(df),
        "total_columns": len(df.columns)
    }

    return render_template(
        "overview.html",
        filename=session_info["filename"],
        preview=preview
    )


# -------------------------------------------------
# ROUTE 5: START ANALYSIS (AGENT)
# -------------------------------------------------
@app.route("/start_analysis", methods=["POST"])
@login_required
def start_analysis():
    try:
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"success": False, "error": "No active session"}), 400

        agent = Agent(session_id)
        success = agent.run_analysis()

        if success:
            # Log Analysis to DB (Privacy: only metadata)
            session_info = storage.get_session(session_id)
            filename = session_info.get("filename", "unknown") if session_info else "unknown"
            
            new_log = AnalysisLog(
                user_id=current_user.id,
                uploaded_file_name=filename,
                report_id=session_id
            )
            db.session.add(new_log)
            db.session.commit()

            return jsonify({
                "success": True,
                "redirect": url_for("analysis")
            })

        return jsonify({
            "success": False,
            "error": "Analysis failed"
        }), 500

    except Exception as e:
        print(f"Agent error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------
# ROUTE 6: ANALYSIS PAGE
# -------------------------------------------------
# -------------------------------------------------
# ROUTE 6: ANALYSIS PAGE
# -------------------------------------------------
@app.route("/analysis")
@login_required
def analysis():
    session_id = session.get("session_id")
    if not session_id:
        return redirect(url_for("upload"))

    session_info = storage.get_session(session_id)
    if not session_info:
        return redirect(url_for("upload"))
    
    # If not completed, redirect to waiting or overview
    if session_info.get("status") != "completed":
        return redirect(url_for("overview"))

    profile_str = storage.get_analysis_result(session_id, "profile")
    charts_str = storage.get_analysis_result(session_id, "charts")
    insights = storage.get_analysis_result(session_id, "insights")

    profile = json.loads(profile_str) if profile_str else {}
    charts = json.loads(charts_str) if charts_str else []
    
    # Debug charts
    print(f"Loading analysis for {session_id}. Found {len(charts)} charts.")

    return render_template(
        "analysis.html",
        filename=session_info.get("filename", "unknown"),
        session_id=session_id,  # Pass session_id for chart loading
        profile=profile,
        charts=charts,
        insights=insights
    )

@app.route("/generate_custom_chart", methods=["POST"])
@login_required
def generate_custom_chart():
    try:
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"success": False, "error": "No session ID found"}), 400

        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        x_col = data.get("x_col")
        y_col = data.get("y_col")
        chart_type = data.get("chart_type", "Auto")

        print(f"Generating custom chart: {x_col} vs {y_col} ({chart_type})")

        session_info = storage.get_session(session_id)
        if not session_info:
            return jsonify({"success": False, "error": "Invalid session"}), 400

        # Load DF
        clean_path = os.path.join(config.TEMP_FOLDER, session_id, f"{session_id}_cleaned.csv")
        if os.path.exists(clean_path):
            df = pd.read_csv(clean_path)
        else:
            df = storage.load_dataframe(session_info["filepath"])

        if df is None or df.empty:
             return jsonify({"success": False, "error": "Data could not be loaded"}), 400

        # Use Analyzer
        from core.analyzer import DataAnalyzer
        analyzer = DataAnalyzer(df, session_id)
        
        result = analyzer.create_custom_chart(x_col, y_col, chart_type)
        
        if result and analyzer.charts:
            # Update session charts storage so it appears in report
            charts_str = storage.get_analysis_result(session_id, "charts")
            current_charts = json.loads(charts_str) if charts_str else []
            
            # Get the chart object we just created
            new_chart = analyzer.charts[-1]
            current_charts.append(new_chart)
            
            # Save back - Charts list should be simple JSON types (strings mostly)
            try:
                storage.save_analysis_result(session_id, "charts", json.dumps(current_charts))
            except TypeError:
                 def default(o): return str(o)
                 storage.save_analysis_result(session_id, "charts", json.dumps(current_charts, default=default))
            
            return jsonify({
                "success": True, 
                "session_id": session_id, 
                "filename": result['filename'],
                "code": result.get('code', '')
            })

        return jsonify({"success": False, "error": "Chart generation failed"}), 500



    except Exception as e:
        print(f"Error in generate_custom_chart: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500



# -------------------------------------------------
# ROUTE 7: FINAL REPORT PAGE
# -------------------------------------------------
@app.route("/report")
@login_required
def report():
    session_id = session.get("session_id")
    if not session_id:
        return redirect(url_for("upload"))

    session_info = storage.get_session(session_id)
    if not session_info or session_info["status"] != "completed":
        return redirect(url_for("overview"))

    report_data = json.loads(
        storage.get_analysis_result(session_id, "report") or "{}"
    )
    
    # Load separate charts list (which includes custom ones)
    charts_str = storage.get_analysis_result(session_id, "charts")
    charts = json.loads(charts_str) if charts_str else []

    return render_template(
        "report.html",
        filename=session_info["filename"],
        session_id=session_id,
        report=report_data,
        charts=charts
    )



# -------------------------------------------------
# ROUTE 8: SERVE CHART IMAGES
# -------------------------------------------------
@app.route("/charts/<session_id>/<filename>")
@login_required
def serve_chart(session_id, filename):
    # Privacy First: Serve from temp session folder
    # Privacy First: Serve from temp session folder
    chart_path = os.path.join(
        config.TEMP_FOLDER, session_id, filename
    )

    if os.path.exists(chart_path):
        return send_file(chart_path, mimetype="image/png")

    return "Chart not found", 404


# -------------------------------------------------
# ROUTE 9: RESET SESSION (PRIVACY CLEANUP)
# -------------------------------------------------
@app.route("/new_analysis")
@login_required
def new_analysis():
    session_id = session.get("session_id")
    if session_id:
        # Secure Wipe: Delete all temporary files for this session
        storage.clear_session_data(session_id)
        session.pop("session_id", None)
        
    return redirect(url_for("upload"))


# -------------------------------------------------
# ERROR HANDLERS
# -------------------------------------------------
@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "success": False,
        "error": f"File too large (max {config.MAX_FILE_SIZE // (1024*1024)} MB)"
    }), 413


@app.errorhandler(404)
def not_found(error):
    return redirect(url_for("get_started"))


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500


# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == "__main__":
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)
