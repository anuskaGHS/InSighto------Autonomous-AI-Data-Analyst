from core.llm_client import LLMClient

def run_llm_test():
    print("\n==============================")
    print(" REAL-WORLD LLM TEST STARTED ")
    print("==============================\n")

    llm = LLMClient()

    # Realistic business context
    context = """
    You are a senior data analyst for an e-commerce company.
    The company sells products across multiple regions and categories.
    Your job is to analyze sales performance and give insights to management.
    """

    # Realistic data summary (like output from profiling step)
    data_summary = """
    Dataset Overview:
    - Total Records: 24,000
    - Time Period: Jan 2023 to Dec 2023
    - Regions: North, South, East, West
    - Categories: Electronics, Clothing, Home, Beauty

    Key Metrics:
    - Total Revenue: $3.2M
    - Average Monthly Revenue: $266,000
    - Highest Revenue Month: November ($420,000)
    - Lowest Revenue Month: February ($145,000)

    Observations:
    - Electronics contributes ~45% of total revenue
    - West region shows highest profit margin
    - South region has high sales volume but low profit
    """

    try:
        response = llm.generate_insights(
            context=context,
            data_summary=data_summary
        )

        print("✅ LLM RESPONSE RECEIVED\n")
        print("----- AI GENERATED INSIGHTS -----\n")
        print(response)
        print("\n---------------------------------\n")

    except Exception as e:
        print("❌ LLM TEST FAILED")
        print("Error:", str(e))

    print("==============================")
    print(" REAL-WORLD LLM TEST ENDED ")
    print("==============================\n")


if __name__ == "__main__":
    run_llm_test()
