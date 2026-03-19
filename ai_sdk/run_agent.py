import os
import sys
from ai_sdk import AISdk

def main():
    # Use the mcp subdirectory's expected environment variables
    # These are typically set via `source ~/.openmetadata/setEnv.sh`
    api_base = os.getenv("API_BASE")
    token = os.getenv("TOKEN")

    if not api_base or not token:
        print("❌ Error: Missing environment variables (TOKEN or API_BASE).")
        print("Please ensure they are set in your environment (e.g. source ~/.openmetadata/setEnv.sh).")
        sys.exit(1)

    # Clean up the api_base if it includes /api/v1 so it just points to the host
    # AI SDK generally expects the base host URL
    host = api_base.split("/api/v1")[0] if "/api/v1" in api_base else api_base
    host = host.rstrip('/')

    print(f"Initializing AISdk with host: {host}")
    
    # Initialize the client using the mapped environment variables
    client = AISdk(
        host=host,
        token=token
    )

    print("Invoking DataQualityPlannerAgent...")
    try:
        # Invoke an agent
        response = client.agent("DataQualityPlannerAgent").call(
            "What data quality tests should I add for the customers table?"
        )
        print("\n=== Agent Response ===")
        print(response.response)
        print("======================\n")

        # Stream responses in real time
        print("Streaming response for 'Analyze the orders table':")
        # Ensure we flush the output to see it in real-time
        for event in client.agent("DataQualityPlannerAgent").stream("Analyze the orders table"):
            if event.type == "content":
                print(event.content, end="", flush=True)
        print("\n")
                
    except Exception as e:
        print(f"❌ Error communicating with AI SDK: {e}")

if __name__ == "__main__":
    main()
