import os
import time
import requests

API_KEY = os.getenv("FREELLM_API_KEY")

BASE_URL = "http://127.0.0.1:31415/v1"
MODEL = "auto"


def main():
    print("\n======================================")
    print("      FREELLMAPI LLM TEST")
    print("======================================\n")

    if not API_KEY:
        print("❌ FREELLM_API_KEY is not set.")
        print()
        print("PowerShell:")
        print('$env:FREELLM_API_KEY="YOUR_FULL_API_KEY"')
        return

    print("API key loaded:", API_KEY[:12] + "..." if len(API_KEY) > 12 else "***")
    print("Base URL:", BASE_URL)
    print("Model:", MODEL)
    print()

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Extract the applicant name from this text. "
                    "Return only the name.\n\n"
                    "Applicant Name: SHREE SHYAM BAJAJ"
                ),
            }
        ],
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    print("Sending request to FreeLLMAPI...")
    start = time.perf_counter()

    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )

        elapsed = time.perf_counter() - start

        print(f"\n⏱️ API time: {elapsed:.2f} seconds")
        print("HTTP status:", response.status_code)

        print("\n========== RAW RESPONSE ==========")
        print(response.text)
        print("==================================")

        if response.ok:
            try:
                data = response.json()

                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                )

                print("\n========== MODEL OUTPUT ==========")
                print(content)
                print("==================================")

            except Exception as e:
                print("\n⚠️ Could not parse JSON:")
                print(e)

        else:
            print("\n❌ API request failed.")

            if response.status_code == 401:
                print(
                    "\nThe API key was rejected.\n"
                    "Check that you copied the COMPLETE Unified API key "
                    "from FreeLLMAPI."
                )

    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to FreeLLMAPI.")
        print("Make sure FreeLLMAPI is running on:")
        print(BASE_URL)

    except requests.exceptions.Timeout:
        print("\n❌ Request timed out.")

    except Exception as e:
        print("\n❌ Unexpected error:")
        print(repr(e))


if __name__ == "__main__":
    main()