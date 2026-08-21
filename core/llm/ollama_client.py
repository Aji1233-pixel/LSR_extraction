import os
import time

from ollama import Client


class OllamaClient:
    """
    Central Ollama client.

    Supports different JSON schemas for different extraction tasks.
    """

    def __init__(self):

        self.host = os.getenv(
            "OLLAMA_HOST",
            "http://localhost:11434"
        )

        self.model = os.getenv(
            "OLLAMA_MODEL",
            "qwen2.5:3b"
        )

        self.client = Client(
            host=self.host
        )

    def generate(
        self,
        prompt: str,
        response_schema: dict | None = None
    ) -> str:
        """
        Send prompt to Ollama.

        Args:
            prompt:
                Prompt sent to the model.

            response_schema:
                Optional JSON schema for structured output.

        Returns:
            Raw JSON string returned by Ollama.
        """

        if not prompt or not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        start_time = time.perf_counter()

        try:

            # ------------------------------------------------
            # Ollama response format
            # ------------------------------------------------

            if response_schema is not None:
                response_format = response_schema
            else:
                response_format = "json"

            # ------------------------------------------------
            # Ollama request
            # ------------------------------------------------

            response = self.client.chat(

                model=self.model,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                format=response_format,

                options={
                    "temperature": 0,

                    # Keep context large enough for LSR OCR text.
                    "num_ctx": 8192,

                    # Document extraction needs more output
                    # than the basic 7-field extraction.
                    "num_predict": 1200,
                }
            )

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print(
                f"⏱️ Ollama API response: "
                f"{elapsed:.2f} seconds"
            )

            content = response.message.content

            print(
                "\n========== RAW OLLAMA RESPONSE =========="
            )

            print(content)

            print(
                "=========================================\n"
            )

            if not content or not content.strip():

                raise RuntimeError(
                    "Ollama returned an empty response."
                )

            return content

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print(
                f"❌ Ollama failed after "
                f"{elapsed:.2f} seconds"
            )

            raise RuntimeError(
                f"Failed to communicate with Ollama: {exc}"
            ) from exc