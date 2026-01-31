# InSighto - Autonomous Data Analyst Agent 

**InSighto** is an intelligent, autonomous data analysis platform that turns raw numbers into actionable business intelligence. Powered by Advanced LLMs (Large Language Models) and Python's robust data science stack, InSighto acts as a virtual data scientist—automatically cleaning, profiling, visualizing, and interpreting your data.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

##  Key Features

*   **Autonomous AI Agent**: The core engine understands the context of your data, deciding which analysis techniques to apply without valid user input.
*   **Smart Data Cleaning**: Automatically handles missing values, duplicates, and correct data types, generating a "Cleaning Report" to show exactly what was changed.
*   **Dynamic Visualization Generation**: Instead of static charts, the AI writes and executes code to generate perfectly tailored visualizations (Heatmaps, Distributions, Boxplots, etc.) based on the data's unique characteristics.
*   **Automated Reporting**: Produces a professional, structured executive report containing:
    *   Executive Summary
    *   Key Observations & Trends
    *   Strategic Recommendations
    *   Data Quality Assessment
*   **Multi-LLM Support**: Built to be flexible—works with **Groq (Llama-3)** for blazing-fast inference, **OpenAI (GPT-4)**, or **Ollama** for local privacy.

---

## Tech Stack

*   **Backend Framework**: Flask (Python)
*   **Data Processing**: Pandas, NumPy
*   **Visualization**: Matplotlib, Seaborn
*   **AI Engine**: Groq API (Llama-3.1), OpenAI API, Ollama
*   **Database**: SQLite (SQLAlchemy)
*   **Frontend**: HTML5, CSS3, JavaScript (Jinja2 Templates)

---

## Installation & Setup

Follow these steps to set up the project locally.

### Prerequisites
*   Python 3.10 or higher
*   Git

### 1. Clone the Repository
```bash
git clone (https://github.com/anuskaGHS/InSighto------Autonomous-AI-Data-Analyst)
cd InSighto
```

### 2. Create a Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and add your API keys. You can choose your preferred LLM provider.

**Example `.env` file:**
```env
# Flask Settings
SECRET_KEY=your_secret_key
FLASK_DEBUG=True

# LLM Provider (groq, openai, or ollama)
# If using Groq:
GROQ_API_KEY=gsk_your_groq_key_here

# If using OpenAI:
# OPENAI_API_KEY=sk-...
```

### 5. Run the Application
```bash
python app.py
```
The application will start at `http://localhost:5000`.

---

##  How to Use

1.  **Register/Login**: Create a local account to secure your session.
2.  **Upload Data**: Drag and drop your CSV or Excel file (`.csv`, `.xlsx`).
3.  **Overview**: View a preview of your raw data to confirm it loaded correctly.
4.  **Start Analysis**: Click the "Start AI Analysis" button. The agent will:
    *   Sanitize the dataset.
    *   Run statistical profiling.
    *   Generate relevent charts.
    *   Draft the final report.
5.  **View Report**: Explore the interactive dashboard containing the Executive Summary, Charts, and Recommendations.

---

##  Project Structure

```
InSighto/
├── core/                   # Core Logic Modules
│   ├── agent.py            # Main Orchestrator
│   ├── analyzer.py         # Visualization Engine
│   ├── cleaner.py          # Data Cleaning Logic
│   ├── llm_client.py       # LLM Interface (Groq/OpenAI/Ollama)
│   └── profiler.py         # Statistical Profiling
├── storage/                # Database & Temp Files
├── templates/              # HTML Templates
├── static/                 # CSS/JS Assets
├── app.py                  # Main Flask App Entry Point
├── config.py               # Configuration & Settings
└── requirements.txt        # Project Dependencies
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request
