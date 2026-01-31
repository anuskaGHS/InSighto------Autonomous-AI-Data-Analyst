import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import os
import config
from core.llm_client import LLMClient
import traceback

class DataAnalyzer:
    """Performs statistical analysis and generates charts"""
    
    def __init__(self, df, session_id):
        """Initialize with DataFrame and session ID"""
        self.df = df
        self.session_id = session_id
        self.charts = []
        self.llm = LLMClient()
        
        # Create charts directory
        # Privacy First: Charts stored in session's temp folder (FLAT STRUCTURE)
        self.charts_dir = os.path.join(config.TEMP_FOLDER, session_id)
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (config.CHART_WIDTH, config.CHART_HEIGHT)
    
    def analyze(self):
        """Run complete analysis pipeline (AI Driven)"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object']).columns.tolist()

        # Goal: Generate 5 high-value charts
        # Strategy: 
        # 1. 1x Distribution (Histogram) of most interesting numeric col
        # 2. 1x Count (Bar) of most interesting categorical col
        # 3. 1x Correlation Heatmap (if enough numeric)
        # 4. 1x Boxplot Comparison (if enough numeric)
        # 5. 1x Scatter/Line (Relationship) - AI suggested
        
        count = 0

        # 1. Trend/Correlation (Heatmap)
        if len(numeric_cols) > 1 and count < 5:
            try:
                context = f"Numeric columns: {numeric_cols}"
                code = self.llm.generate_chart_code(context, numeric_cols, "Correlation Heatmap")
                if code:
                    self._execute_plot_code(code, "Correlation Heatmap", "correlation_heatmap")
                    count += 1
            except Exception: pass

        # 2. Key Distribution (Histogram)
        if len(numeric_cols) > 0 and count < 5:
            # Pick column with highest variance or simply first
            col = numeric_cols[0] 
            self._create_histogram(col)
            count += 1

        # 3. Categorical Insights (Bar)
        if len(categorical_cols) > 0 and count < 5:
            col = categorical_cols[0]
            self._create_bar_chart(col)
            count += 1
            
        # 4. Box Plot (Outliers/Spread)
        if len(numeric_cols) > 0 and count < 5:
            self._create_boxplot(numeric_cols[:5]) # Top 5 cols
            count += 1

        # 5. AI Suggested Relationship
        if len(numeric_cols) > 1 and count < 5:
            try:
                context = f"Find an interesting relationship between these columns: {numeric_cols}."
                code = self.llm.generate_chart_code(context, numeric_cols, "Scatter Plot or Line Chart")
                if code:
                    self._execute_plot_code(code, "Key Relationship Analysis", "ai_relationship_plot")
                    count += 1
            except Exception: pass
            
        return self.charts

    def create_custom_chart(self, x_col, y_col=None, chart_type="Auto"):
        """Generate a custom chart based on user selection"""
        try:
            context = f"Columns available: {list(self.df.columns)}"
            cols = f"{x_col}" + (f", {y_col}" if y_col else "")
            
            code = self.llm.generate_chart_code(context, cols, chart_type)
            
            if code:
                filename = f"custom_{x_col}_{chart_type}.png".replace(" ", "_")
                if self._execute_plot_code(code, f"{chart_type} of {cols}", filename.replace(".png", "")):
                    return {'filename': filename, 'code': code}
            return None
        except Exception as e:
            print(f"Custom chart error: {e}")
            return None

    def _execute_plot_code(self, code, title, filename_base):
        """Execute plotting code and save the result"""
        try:
            # Create a localized environment
            local_env = {
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,
                'df': self.df
            }
            
            # Execute the code
            plt.figure(figsize=(config.CHART_WIDTH, config.CHART_HEIGHT))
            exec(code, {}, local_env)
            
            # Save
            filename = f"{filename_base}.png"
            filepath = os.path.join(self.charts_dir, filename)
            
            plt.title(title) # Ensure title is set if code didn't
            plt.tight_layout()
            plt.savefig(filepath, dpi=config.CHART_DPI, bbox_inches='tight')
            plt.close()
            
            self.charts.append({
                'type': 'custom',
                'title': title,
                'filename': filename,
                'filepath': filepath,
                'description': f'AI generated chart: {title}',
                'code': code
            })
            return True
            
        except Exception as e:
            print(f"Error executing plot code: {e}")
            traceback.print_exc()
            plt.close()
            return False

    # --- Basic Implementations (Reliable Fallbacks) ---
    def _create_histogram(self, column):
        code = f"""import seaborn as sns
import matplotlib.pyplot as plt

# Generate Histogram
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='{column}', kde=True, color='skyblue')
plt.title('Distribution of {column}')
plt.tight_layout()"""
        try:
            plt.figure(figsize=(config.CHART_WIDTH, config.CHART_HEIGHT))
            sns.histplot(data=self.df, x=column, kde=True, color='skyblue')
            self._save_plot(f'Distribution of {column}', f'hist_{column}', code)
        except Exception as e: print(f"Hist error: {e}")

    def _create_bar_chart(self, column):
        code = f"""import seaborn as sns
import matplotlib.pyplot as plt

# Generate Bar Chart (Top 10)
plt.figure(figsize=(10, 6))
top_10 = df['{column}'].value_counts().head(10).index
sns.countplot(
    data=df[df['{column}'].isin(top_10)], 
    x='{column}', 
    order=top_10, 
    palette='viridis'
)
plt.xticks(rotation=45)
plt.title('Top categories in {column}')
plt.tight_layout()"""
        try:
            plt.figure(figsize=(config.CHART_WIDTH, config.CHART_HEIGHT))
            # Get top 10
            top_10 = self.df[column].value_counts().head(10).index
            sns.countplot(data=self.df[self.df[column].isin(top_10)], x=column, order=top_10, palette='viridis')
            plt.xticks(rotation=45)
            self._save_plot(f'Top categories in {column}', f'bar_{column}', code)
        except Exception as e: print(f"Bar error: {e}")

    def _create_boxplot(self, numeric_cols):
        cols_to_plot = numeric_cols[:5]
        code = f"""import matplotlib.pyplot as plt

# Generate Boxplot
plt.figure(figsize=(10, 6))
cols_to_plot = {cols_to_plot}
data_to_plot = [df[col].dropna() for col in cols_to_plot]

bp = plt.boxplot(data_to_plot, labels=cols_to_plot, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightblue')

plt.xticks(rotation=45)
plt.title('Box Plot Distribution')
plt.tight_layout()"""
        try:
            plt.figure(figsize=(config.CHART_WIDTH, config.CHART_HEIGHT))
            
            # Prepare data (limit to first 5 for readability if passed more)
            cols_to_plot = numeric_cols[:5]
            data_to_plot = [self.df[col].dropna() for col in cols_to_plot]
            
            # Plot boxplot
            bp = plt.boxplot(data_to_plot, labels=cols_to_plot, patch_artist=True)
            
            # Color the boxes
            for patch in bp['boxes']:
                patch.set_facecolor('lightblue')
            
            plt.xticks(rotation=45)
            self._save_plot('Box Plot Distribution', 'boxplot_comparison', code)
        except Exception as e: print(f"Boxplot error: {e}")

    def _save_plot(self, title, filename_base, code=None):
        filename_base = filename_base.replace(" ", "_").replace("/", "").replace("\\", "")
        filename = f"{filename_base}.png"
        filepath = os.path.join(self.charts_dir, filename)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(filepath, dpi=config.CHART_DPI, bbox_inches='tight')
        plt.close()
        
        self.charts.append({
            'type': 'basic',
            'title': title,
            'filename': filename,
            'filepath': filepath,
            'description': title,
            'code': code
        })
