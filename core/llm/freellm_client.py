import os
import time

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


class FreeLLMClient:
    """
    Client for FreeLLMAPI.

    Uses the OpenAI-compatible /v1/chat/completions endpoint.
    """

    def __init__(self):

        self.api_key = os.getenv(
            "FREELLM_API_KEY"
        )

        self.base_url = os.getenv(
            "FREELLM_BASE_URL",
            "http://localhost:3001/v1"
        )

        self.model = os.getenv(
            "FREELLM_MODEL",
            "auto"
        )

        if not self.api_key:
            raise RuntimeError(
                "FREELLM_API_KEY is not configured "
                "in the .env file."
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to FreeLLMAPI and return
        the generated text.
        """

        if not prompt or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        start_time = time.perf_counter()

        try:

            response = self.client.chat.completions.create(
                model=self.model,

                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],

                temperature=0,

                max_tokens=1500,
            )

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print(
                f"⏱️ FreeLLM API response: "
                f"{elapsed:.2f} seconds"
            )

            if not response.choices:
                raise RuntimeError(
                    "FreeLLM returned no choices."
                )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            if not content or not content.strip():
                raise RuntimeError(
                    "FreeLLM returned an empty response."
                )

            print(
                "\n========== RAW FREELLM RESPONSE =========="
            )

            print(content)

            print(
                "===========================================\n"
            )

            return content

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print(
                f"❌ FreeLLM failed after "
                f"{elapsed:.2f} seconds"
            )

            raise RuntimeError(
                f"FreeLLM API request failed: {exc}"
            ) from exc