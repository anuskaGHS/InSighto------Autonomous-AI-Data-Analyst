import requests
import json
import config


class LLMClient:
    """Handles communication with LLM (OpenAI-compatible & Ollama APIs)"""

    def __init__(self):
        """Initialize LLM client with config settings"""
        self.provider = config.LLM_PROVIDER
        self.base_url = config.LLM_BASE_URL
        self.model = config.LLM_MODEL
        self.api_key = config.LLM_API_KEY
        self.available = True

    def _check_availability(self):
        """Check if LLM is available and responding"""
        try:
            response = self._make_request(
                prompt="Hello",
                max_tokens=10,
                temperature=0.7
            )
            return response is not None
        except Exception as e:
            print(f"LLM not available: {e}")
            return False

    def _make_request(self, prompt, max_tokens=1000, temperature=0.7):
        print("LLM CALLED WITH PROMPT:", prompt[:200])

        """Make a request to the LLM API (Ollama or OpenAI-style)"""
        try:
            # -------------------------------
            # OLLAMA (local)
            # -------------------------------
            if self.provider =="ollama":
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }

                response = requests.post(
                    self.base_url,
                    json=payload,
                    timeout=180
                )

                if response.status_code == 200:
                    print("LLM RAW RESPONSE:", response.text[:500])
                    return response.json().get("response", "").strip()
                else:
                    print(f"Ollama error: {response.status_code} - {response.text}")
                    return None

            # -------------------------------
            # OPENAI / COMPATIBLE
            # -------------------------------
            elif self.provider in ("openai", "groq"):
                endpoint = f"{self.base_url}/chat/completions"

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a professional data analyst. "
                                "Provide clear, accurate insights based only on the data provided. "
                                "Never hallucinate or make up information."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }

                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    print(f"LLM API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            print(f"Error making LLM request: {e}")
            return None

    # ===============================
    # HIGH-LEVEL AGENT FUNCTIONS
    # ===============================

    print(">> generate_insights CALLED")

    def generate_insights(self, context, data_summary):
        if not self.available:
            return self._fallback_insights()

        prompt = f"""
STRICT RESPONSE RULES:
1. OUTPUT FORMAT: Use HTML bullet points (<ul>, <li>) for structure.
2. NO PLAIN PARAGRAPHS: Do not write long blocks of text.
3. BE CONCISE: Direct and to the point.
4. FACTS ONLY: Use only the provided data.

You are analyzing a dataset. Based on the following information, provide clear insights.

DATASET CONTEXT:
{context}

DATA SUMMARY:
{data_summary}

Please provide the following sections (use <h3> for headers):
<h3>1. Key Observations</h3>
(Provide 3-5 bullet points)

<h3>2. Trends & Patterns</h3>
(Provide relevant bullet points)

<h3>3. Data Quality Notes</h3>
(Provide relevant bullet points)

<h3>4. Recommended Actions</h3>
(Provide relevant bullet points)

Keep your response clean, structured, and HTML-formatted.
"""
        response = self._make_request(prompt, max_tokens=1000, temperature=0.7)
        return response if response else self._fallback_insights()

    def generate_executive_summary(self, analysis_results):
        if not self.available:
            return self._fallback_summary()

        prompt = f"""
        You are creating a professional executive summary for a data analysis report.
        
        ANALYSIS RESULTS:
        {analysis_results}
        
        INSTRUCTIONS:
        1. Write a structured summary using HTML tags.
        2. Start with a brief introductory paragraph (1-2 sentences).
        3. Use an unordered list (<ul>) with <li> tags for key findings.
        4. Use <b>bold tags</b> to highlight important metrics or keywords.
        5. DO NOT use emojis.
        6. Keep it concise, high-level, and easy to scan.
        
        Structure:
        <p>Introduction...</p>
        <ul>
            <li><b>Key Finding 1:</b> Detail...</li>
            <li><b>Key Finding 2:</b> Detail...</li>
        </ul>
        """
        response = self._make_request(prompt, max_tokens=800, temperature=0.7)
        return response if response else self._fallback_summary()

    def generate_recommendations(self, analysis_results):
        if not self.available:
            return self._fallback_recommendations()

        prompt = f"""
        Based on the data analysis, provide 3-5 strategic recommendations.
        
        ANALYSIS RESULTS:
        {analysis_results}
        
        INSTRUCTIONS:
        1. Output as an HTML unordered list (<ul>).
        2. Each recommendation <li> should start with a <b>Bold Strategy Title:</b>.
        3. Be actionable and professional.
        4. DO NOT use emojis.
        5. Format exactly as HTML list items.
        
        Example:
        <ul>
            <li><b>Optimize Inventory:</b> Based on sales trends...</li>
        </ul>
        """
        response = self._make_request(prompt, max_tokens=600, temperature=0.7)
        return response if response else self._fallback_recommendations()

    def explain_chart(self, chart_description, data_context):
        if not self.available:
            return f"This chart shows: {chart_description}"

        prompt = f"""
Explain this chart in simple, plain English (2-3 sentences).

CHART DESCRIPTION:
{chart_description}

DATA CONTEXT:
{data_context}

Focus on what the chart reveals about the data.
"""
        response = self._make_request(prompt, max_tokens=200, temperature=0.7)
        return response if response else f"This chart shows: {chart_description}"

    def generate_chart_code(self, context, columns, chart_type=None):
        if not self.available:
            return None

        prompt = f"""
STRICT RULES:
1. OUTPUT: Return ONLY valid Python code block.
2. LIBRARIES: You can use pandas (pd), matplotlib.pyplot (plt), seaborn (sns).
3. CONTEXT: The dataframe is available in variable `df`.
4. OUTPUT FORMAT:
   - Create a figure with `plt.figure(figsize=(10, 6))`
   - Create the plot
   - Set titles and labels
   - Do NOT show the plot (no plt.show())
   - Do NOT save the plot (it will be saved by the caller)

CONTEXT:
{context}

REQUEST:
Generate code for a reasonable chart using columns: {columns}.
Chart Type Preference: {chart_type if chart_type else 'Best fit'}
"""
        response = self._make_request(prompt, max_tokens=600, temperature=0.5)
        
        # Clean response to get only code
        if response:
            code = response.replace("```python", "").replace("```", "").strip()
            return code
        return None

    # ===============================
    # FALLBACKS
    # ===============================

    def _fallback_insights(self):
        return """
**Insights (Basic Analysis):**

The LLM service is currently unavailable. Here are basic observations:

1. The dataset has been successfully loaded and cleaned
2. Statistical analysis has been performed on all numeric columns
3. Visualizations have been generated for key variables
4. Please review the charts and statistics for detailed information
"""

    def _fallback_summary(self):
        return """
This report presents an analysis of the uploaded dataset. The data has been processed,
cleaned, and analyzed to extract key statistics and patterns.
"""

    def _fallback_recommendations(self):
        return """
1. Review the statistical summaries for each variable
2. Examine the visualizations to identify patterns
3. Check for any data quality issues
4. Consider domain-specific analysis
5. Use insights to guide decisions
"""