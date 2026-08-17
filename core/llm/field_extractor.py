import json
import time
from core.config.fields import REQUIRED_FIELDS
from .ollama_client import OllamaClient


class FieldExtractor:
    """Extract required fields from document text."""

    def __init__(self):
        self.ollama = OllamaClient()

    def extract_fields(self, text: str) -> dict:

        print("\n" + "=" * 50)
        print("LLM EXTRACTION STARTED")
        print("=" * 50)

        print(
            f"📝 Input characters: {len(text)}"
        )

        print(
            f"📝 Input words: {len(text.split())}"
        )

        # -------------------------------
        # Prompt construction
        # -------------------------------

        prompt_start = time.perf_counter()

        prompt = self._build_prompt(text)

        prompt_time = time.perf_counter() - prompt_start

        print(
            f"⏱️ Prompt construction: "
            f"{prompt_time:.2f} seconds"
        )

        print(
            f"📝 Prompt characters: {len(prompt)}"
        )

        # -------------------------------
        # Ollama
        # -------------------------------

        ollama_start = time.perf_counter()

        response = self.ollama.generate(prompt)

        ollama_time = time.perf_counter() - ollama_start

        print(
            f"⏱️ LLM extraction: "
            f"{ollama_time:.2f} seconds"
        )

        # -------------------------------
        # JSON parsing
        # -------------------------------

        parse_start = time.perf_counter()

        result = self._parse_response(response)

        parse_time = time.perf_counter() - parse_start

        print(
            f"⏱️ JSON parsing: "
            f"{parse_time:.2f} seconds"
        )

        print("=" * 50)

        return result
    def _build_prompt(self, text: str) -> str:

        return f"""
    Extract exactly these 7 fields from the legal property document.

    Return only JSON matching the required structure.

    Field rules:

    1. lsr_date:
    Use the date written after "Dated:" near the beginning of the legal opinion.

    2. company_name:
    Use the organization name appearing immediately after "To,".
    Example: Bajaj Finance Limited.

    3. applicant_name:
    Use ONLY the name after:
    "Name of the Applicant / Borrower/s:"
    Do NOT include co-applicants.

    4. co_applicant_name:
    Use ONLY the names after:
    "Name of the Co - Applicant / Borrower/s:"
    Include all co-applicants.

    5. property_owner:
    Use ONLY the name after:
    "Name of the Property Owner:"

    6. application_number:
    Use the value after:
    "APP. NO."

    7. property_description:
    Extract the complete "Property Address and Description".
    Include property identification, survey/khewat/khatoni details,
    extent, measurements and boundaries when present.

    Rules:
    - Do not guess.
    - Preserve names and numbers exactly.
    - If a field cannot be found, return null.
    - Do not combine different fields.
    - Return JSON only.

    DOCUMENT:
    {text}
    """.strip()

    def _parse_response(self, response: str) -> dict:
        """Convert LLM JSON response into a Python dictionary."""

        if not response or not response.strip():
            raise RuntimeError(
                "LLM returned an empty response."
            )

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"LLM returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "LLM response must be a JSON object."
            )

        # Ensure our application always returns
        # the predefined fields.
        result = {
            field: data.get(field)
            for field in REQUIRED_FIELDS
        }
        print(result)
        return result