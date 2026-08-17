import os
import time

from ollama import Client


class OllamaClient:

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

    def generate(self, prompt: str) -> str:

        if not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

        start_time = time.perf_counter()

        try:
            EXTRACTION_SCHEMA = {
                "type": "object",
                "properties": {
                    "lsr_date": {
                        "type": ["string", "null"]
                    },
                    "company_name": {
                        "type": ["string", "null"]
                    },
                    "applicant_name": {
                        "type": ["string", "null"]
                    },
                    "co_applicant_name": {
                        "type": ["string", "null"]
                    },
                    "property_owner": {
                        "type": ["string", "null"]
                    },
                    "application_number": {
                        "type": ["string", "null"]
                    },
                    "property_description": {
                        "type": ["string", "null"]
                    }
                },
                "required": [
                    "lsr_date",
                    "company_name",
                    "applicant_name",
                    "co_applicant_name",
                    "property_owner",
                    "application_number",
                    "property_description"
                ]
            }
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                format="json",
                options={
                "temperature": 0,
                "num_ctx": 8192,
                "num_predict": 700,
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
            

            if not content.strip():
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