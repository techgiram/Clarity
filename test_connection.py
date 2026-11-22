import time
from backend.services.llm_service import get_llm

print("1. Loading LLM service...")
llm = get_llm()

max_retries = 3
for attempt in range(1, max_retries + 1):
    try:
        print(f"2. Sending message to Gemini (Attempt {attempt}/{max_retries})...")
        response = llm.invoke("Hi", timeout=15)
        print("3. Success! Response received:")
        print(response.content)
        break
    except Exception as e:
        print(f"Error on attempt {attempt}: {e}")
        if attempt < max_retries:
            print("Waiting 3 seconds before retrying...")
            time.sleep(3)
        else:
            print("All retries failed due to Google server high demand. Please try running again in a minute.")