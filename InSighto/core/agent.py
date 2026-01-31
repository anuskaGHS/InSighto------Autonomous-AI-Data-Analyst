import json
from datetime import datetime
import pandas as pd
import config

from core.storage import Storage
from core.llm_client import LLMClient
from core.report_generator import ReportGenerator
from core.profiler import DataProfiler
from core.cleaner import DataCleaner
from core.analyzer import DataAnalyzer
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    """ Custom encoder for NumPy types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class Agent:
    """
    Autonomous Data Analyst Agent
    Controls the full analysis workflow
    """

    def __init__(self, session_id):
        self.session_id = session_id
        self.storage = Storage()
        self.llm = LLMClient()

        session_info = self.storage.get_session(session_id)
        if session_info:
            self.filename = session_info["filename"]
            self.filepath = session_info["filepath"]
        else:
            self.filename = None
            self.filepath = None

    def run_analysis(self):
        """
        Main execution pipeline
        """
        if not self.filename or not self.filepath:
            print(f"Session {self.session_id} not found.")
            return False

        try:
            # Update status
            self.storage.update_session_status(self.session_id, "analyzing")

            # -------------------------------------------------
            # STEP 1: Load Dataset
            # -------------------------------------------------
            print(f"Loading dataset: {self.filepath}")
            df = self.storage.load_dataframe(self.filepath)
            if df is None or df.empty:
                raise ValueError("Dataset could not be loaded or is empty")

            # -------------------------------------------------
            # STEP 2: Data Cleaning
            # -------------------------------------------------
            print("Cleaning data...")
            cleaner = DataCleaner(df)
            cleaned_df, cleaning_report = cleaner.clean()
            cleaning_summary = cleaner.get_cleaning_summary()

            # Save cleaned dataset
            self.storage.save_dataframe(cleaned_df, self.session_id, 'cleaned')

            # -------------------------------------------------
            # STEP 3: Data Profiling
            # -------------------------------------------------
            print("Profiling data...")
            profiler = DataProfiler(cleaned_df)
            profile = profiler.generate_profile()
            profile_summary_text = profiler.get_summary_text()

            # -------------------------------------------------
            # STEP 4: generate Charts
            # -------------------------------------------------
            print("Generating charts...")
            analyzer = DataAnalyzer(cleaned_df, self.session_id)
            charts = analyzer.analyze()

            # -------------------------------------------------
            # STEP 5: AI Insights & Content Generation
            # -------------------------------------------------
            print("Generating AI insights...")
            
            # Prepare context for LLM
            context = f"Dataset: {self.filename}\n\nCleaning Summary:\n{json.dumps(cleaning_summary['report'], indent=2, cls=NumpyEncoder)}"
            
            # Use profile summary for dense information
            data_summary = json.dumps(profile, indent=2, cls=NumpyEncoder)

            # Generate Insights
            insights = self.llm.generate_insights(
                context=context,
                data_summary=data_summary
            )

            # Generate Executive Summary
            exec_summary = self.llm.generate_executive_summary(
                analysis_results=f"{profile_summary_text}\n\nTop Insights:\n{insights}"
            )

            # Generate Recommendations
            recommendations = self.llm.generate_recommendations(
                analysis_results=f"{profile_summary_text}\n\nInsights:\n{insights}"
            )

            # -------------------------------------------------
            # STEP 6: Build Structured Report
            # -------------------------------------------------
            print("Building final report...")
            report_generator = ReportGenerator(
                session_id=self.session_id,
                filename=self.filename
            )

            report_generator.add_dataset_overview(profile)
            report_generator.add_data_quality(cleaning_summary)
            report_generator.add_statistics(profile)
            report_generator.add_visualizations(charts)
            report_generator.add_insights(insights)
            report_generator.add_executive_summary(exec_summary)
            report_generator.add_recommendations(recommendations)

            report = report_generator.get_report()

            # -------------------------------------------------
            # STEP 7: Persist Results
            # -------------------------------------------------
            print("Saving results...")
            
            # Save individual components (for specific UI views)
            self.storage.save_analysis_result(
                self.session_id, "profile", json.dumps(profile, cls=NumpyEncoder)
            )
            self.storage.save_analysis_result(
                self.session_id, "charts", json.dumps(charts, cls=NumpyEncoder)
            )
            self.storage.save_analysis_result(
                self.session_id, "insights", insights
            )
            
            # Save full report
            self.storage.save_analysis_result(
                self.session_id, "report", json.dumps(report, cls=NumpyEncoder)
            )

            # -------------------------------------------------
            # STEP 8: Mark Session Completed
            # -------------------------------------------------
            self.storage.update_session_status(self.session_id, "completed")
            print("Analysis completed successfully.")

            return True

        except Exception as e:
            print(f"Agent error in run_analysis: {e}")
            import traceback
            traceback.print_exc()
            self.storage.update_session_status(self.session_id, "error")
            return False
