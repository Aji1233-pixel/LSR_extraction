import requests
import os

BASE_URL = "http://127.0.0.1:31415/v1"
API_KEY = os.getenv("FREELLM_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "FREELLM_API_KEY environment variable is not set."
    )

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

print("\n======================================")
print("      FREELLMAPI CONNECTION TEST")
print("======================================")

print("\nChecking available models...")

response = requests.get(
    f"{BASE_URL}/models",
    headers=headers,
    timeout=30,
)

print("Status:", response.status_code)

if response.status_code != 200:
    print(response.text)
    raise SystemExit()

data = response.json()

print("\n========== AVAILABLE MODELS ==========")

for model in data.get("data", []):
    print("Model:", model.get("id"))

print("======================================")