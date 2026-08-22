import os
import sys
import time
import requests
from dotenv import load_dotenv


load_dotenv()

# Ensure UTF-8 output so emoji/log messages don't crash on
# Windows consoles that default to cp1252 (e.g. when run under pytest).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class FreeLLMClient:
    """
    LLM communication layer for FreeLLMAPI.

    Communicates with FreeLLMAPI using an OpenAI-compatible
    /v1/chat/completions endpoint.

    Field/document extraction logic does NOT belong here.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 300,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "FREELLM_BASE_URL",
                "http://127.0.0.1:31415/v1",
            )
        ).rstrip("/")

        self.api_key = (
            api_key
            or os.getenv("FREELLM_API_KEY")
        )

        self.model = (
            model
            or os.getenv(
                "FREELLM_MODEL",
                "auto",
            )
        )

        self.timeout = timeout

    # ============================================================
    # MAIN LLM METHOD
    # ============================================================

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to FreeLLMAPI and return the raw model text.

        Extraction/document-specific logic is intentionally not
        handled here.
        """

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if not self.api_key:
            raise RuntimeError(
                "FREELLM_API_KEY is not configured. "
                "Check your .env file."
            )

        print("\n" + "=" * 60)
        print("FREE LLM API REQUEST")
        print("=" * 60)

        print(f"Base URL : {self.base_url}")
        print(f"Model    : {self.model}")

        # Never print the complete API key.
        print(
            f"API Key  : {self.api_key[:12]}..."
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        max_retries = 3
        for attempt in range(max_retries):
            start_time = time.perf_counter()

            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )

                elapsed = time.perf_counter() - start_time

                print(
                    f"⏱️ FreeLLM API response: "
                    f"{elapsed:.2f} seconds"
                )

                print(
                    f"HTTP status: {response.status_code}"
                )

                # Handle rate limiting with exponential backoff retry
                if response.status_code == 429:
                    wait_time = min(2 ** (attempt + 1), 30)  # 4s, 8s, 16s (capped at 30s)
                    print(f"⚠️ Rate limited (429). Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()

                # ====================================================
                # OPENAI-COMPATIBLE RESPONSE
                # ====================================================

                choices = data.get("choices", [])

                if not choices:
                    raise RuntimeError(
                        "FreeLLMAPI returned no choices."
                    )

                message = choices[0].get(
                    "message",
                    {},
                )

                content = message.get(
                    "content",
                    "",
                )

                if content is None:
                    content = ""

                content = str(content).strip()

                if not content:
                    raise RuntimeError(
                        "FreeLLMAPI returned an empty model response."
                    )

                print("\n========== RAW LLM RESPONSE ==========")
                print(content)
                print("======================================")

                return content

            except requests.exceptions.Timeout as exc:

                elapsed = time.perf_counter() - start_time

                print(
                    f"⏱️ Request timeout after "
                    f"{elapsed:.2f} seconds"
                )

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        "FreeLLMAPI request timed out."
                    ) from exc
                time.sleep(2)
                continue

            except requests.exceptions.ConnectionError as exc:

                elapsed = time.perf_counter() - start_time

                print(
                    f"⏱️ Connection failed after "
                    f"{elapsed:.2f} seconds"
                )

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        "Could not connect to FreeLLMAPI. "
                        "Make sure the FreeLLMAPI service is running."
                    ) from exc
                time.sleep(2)
                continue

            except requests.exceptions.HTTPError as exc:

                status_code = (
                    exc.response.status_code
                    if exc.response is not None
                    else "unknown"
                )

                try:
                    error_body = exc.response.text
                except Exception:
                    error_body = ""

                print("\n========== LLM API ERROR ==========")
                print(f"HTTP status: {status_code}")
                print(error_body)
                print("===================================")

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"FreeLLMAPI returned HTTP "
                        f"{status_code}."
                    ) from exc
                time.sleep(2)
                continue

            except requests.exceptions.RequestException as exc:

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"FreeLLMAPI request failed: {exc}"
                    ) from exc
                time.sleep(2)
                continue

            except ValueError as exc:

                if attempt == max_retries - 1:
                    raise RuntimeError(
                        "FreeLLMAPI returned invalid JSON."
                    ) from exc
                time.sleep(2)
                continue

        raise RuntimeError(f"FreeLLMAPI failed after {max_retries} attempts.")

    # ============================================================
    # BACKWARD-COMPATIBILITY ALIAS
    # ============================================================

    def call_llm(self, prompt: str) -> str:
        """
        Backward-compatible method.

        Existing code that calls client.call_llm(prompt)
        will continue to work.
        """

        return self.generate(prompt)


# ================================================================
# OPTIONAL FUNCTION-LEVEL COMPATIBILITY
# ================================================================

def call_llm(prompt: str) -> str:
    """
    Convenience wrapper for older code that imports:

        from core.llm.freellm_client import call_llm
    """

    client = FreeLLMClient()

    return client.generate(prompt)