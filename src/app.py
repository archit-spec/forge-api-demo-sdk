from forge_sdk import ForgeClient, ForgeError, ReasoningSpeed
import json

def main():
    # Initialize client (will use FORGE_API_KEY environment variable)
    client = ForgeClient()
    
    # The woodchuck prompt
    
    prompt = """
Consider a near-future scenario where atmospheric carbon capture technology becomes highly efficient, capable of removing 1 gigaton of CO2 per year at $100 per ton. However, implementing this technology produces black carbon particulates as a byproduct, which have a stronger but shorter-term warming effect than CO2. If this technology were deployed globally tomorrow, analyze the complex tradeoffs between immediate climate effects versus long-term benefits, considering:

 - The different atmospheric residence times of CO2 (centuries) versus black carbon (weeks)
 - The economic implications for developing nations
 - The potential feedback loops in both atmospheric chemistry and global policy
 - How this might affect international climate agreements and carbon markets

   What would be the optimal deployment strategy to maximize benefit while minimizing risk?

    """

    
    try:
        # Get completion with default settings (medium speed)
        response = client.complete(prompt)
        
        if response.succeeded:
            print(f"\nCompletion succeeded in {response.completion_time:.1f} seconds")
            print("\nResult:")
            print(json.dumps(response.result, indent=2))
        else:
            print(f"\nCompletion failed with status: {response.status}")
            print("\nError details:")
            print(json.dumps(response.result, indent=2))
            
    except ForgeError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
