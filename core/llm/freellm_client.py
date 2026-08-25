import os
import time

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class FreeLLMClient:
    """
    Client for FreeLLM API.

    Uses an OpenAI-compatible API endpoint.

    Configuration is loaded from .env:

        FREELLM_API_KEY
        FREELLM_BASE_URL
        FREELLM_MODEL
    """

    def __init__(self):
        # ========================================================
        # LOAD CONFIGURATION
        # ========================================================

        self.api_key = os.getenv(
            "FREELLM_API_KEY"
        )

        self.base_url = os.getenv(
            "FREELLM_BASE_URL",
            "http://127.0.0.1:31415/v1",
        )

        self.model = os.getenv(
            "FREELLM_MODEL",
            "auto",
        )

        # ========================================================
        # VALIDATE API KEY
        # ========================================================

        if not self.api_key:
            raise RuntimeError(
                "FREELLM_API_KEY is not configured "
                "in the .env file."
            )

        # ========================================================
        # CREATE OPENAI CLIENT
        # ========================================================

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0,
            max_retries=1,
        )

        print(
            "✅ FreeLLM client initialized"
        )

        print(
            f"🌐 FreeLLM URL: {self.base_url}"
        )

        print(
            f"🤖 FreeLLM model: {self.model}"
        )

    # ============================================================
    # GENERATE
    # ============================================================

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Send a prompt to FreeLLM and return generated text.
        """

        if not prompt or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        start_time = time.perf_counter()

        try:

            # ====================================================
            # API REQUEST
            # ====================================================

            response = (
                self.client
                .chat
                .completions
                .create(
                    model=self.model,

                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],

                    temperature=0,

                    max_tokens=4000,
                )
            )

            # ====================================================
            # RESPONSE TIME
            # ====================================================

            elapsed = (
                time.perf_counter()
                - start_time
            )

                print(
                    f"⏱️ FreeLLM API response: "
                    f"{elapsed:.2f} seconds"
                )

                print(
                    f"HTTP status: {response.status_code}"
                )

                # Handle rate limiting with retry
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                    print(f"⚠️ Rate limited (429). Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()

            # ====================================================
            # VALIDATE RESPONSE
            # ====================================================

            if not response:

                raise RuntimeError(
                    "FreeLLM returned no response."
                )

            if not response.choices:

                raise RuntimeError(
                    "FreeLLM returned no choices."
                )

            message = (
                response
                .choices[0]
                .message
            )

            content = (
                message.content
                if message
                else None
            )

            if not content:

                raise RuntimeError(
                    "FreeLLM returned an empty response."
                )

            content = content.strip()

            # ====================================================
            # DEBUG OUTPUT
            # ====================================================

            print(
                "\n========== RAW FREELLM RESPONSE =========="
            )

            print(content)

            print(
                "===========================================\n"
            )

            return content

        # ========================================================
        # ERROR HANDLING
        # ========================================================

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print(
                f"❌ FreeLLM failed after "
                f"{elapsed:.2f} seconds"
            )

            print(
                f"❌ Error: {exc}"
            )

            raise RuntimeError(
                f"FreeLLM API request failed: {exc}"
            ) from exc