import json
import re
import time
from typing import Optional

from core.config.fields import REQUIRED_FIELDS
from .freellm_client import FreeLLMClient


class FieldExtractor:
    """
    Extract the required basic fields from an LSR document.

    Uses FreeLLM through the shared FreeLLMClient.
    """

    def __init__(
        self,
        llm_client: FreeLLMClient,
    ):
        self.llm = llm_client

    # ============================================================
    # MAIN EXTRACTION
    # ============================================================

    def extract_fields(
        self,
        text: str,
    ) -> dict:

        if not text or not text.strip():
            raise ValueError(
                "Document text cannot be empty."
            )

        print("\n" + "=" * 50)
        print("LLM EXTRACTION STARTED")
        print("=" * 50)

        print(
            f"📝 Input characters: {len(text)}"
        )

        print(
            f"📝 Input words: {len(text.split())}"
        )

        start_time = time.perf_counter()

        # --------------------------------------------------------
        # Build prompt
        # --------------------------------------------------------

        prompt = self._build_prompt(text)

        print(
            f"📝 Prompt characters: "
            f"{len(prompt)}"
        )

        print(
            f"⏱️ Prompt construction: "
            f"{time.perf_counter() - start_time:.2f}s"
        )

        # --------------------------------------------------------
        # Call FreeLLM
        # --------------------------------------------------------

        llm_start = time.perf_counter()

        try:

            response = self.llm.generate(
                prompt
            )

        except Exception as exc:

            print(
                f"❌ Field extraction LLM failed: "
                f"{exc}"
            )

            raise RuntimeError(
                f"Field extraction failed: {exc}"
            ) from exc

        llm_time = (
            time.perf_counter()
            - llm_start
        )

        print(
            f"⏱️ LLM extraction: "
            f"{llm_time:.2f} seconds"
        )

        # --------------------------------------------------------
        # Parse response
        # --------------------------------------------------------

        parse_start = time.perf_counter()

        result = self._parse_response(
            response
        )

        parse_time = (
            time.perf_counter()
            - parse_start
        )

        print(
            f"⏱️ JSON parsing: "
            f"{parse_time:.2f} seconds"
        )

        # --------------------------------------------------------
        # Recovery for missing fields
        # --------------------------------------------------------

        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if result.get(field) is None
        ]

        if missing_fields:

            print(
                "⚠️ Missing fields from LLM: "
                f"{missing_fields}"
            )

            # Try deterministic extraction for
            # obvious labelled fields.
            result = self._recover_missing_fields(
                text,
                result,
                missing_fields,
            )

        print(
            "\n========== FINAL EXTRACTED FIELDS =========="
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

        print(
            "============================================\n"
        )

        print("=" * 50)

        return result

    # ============================================================
    # PROMPT
    # ============================================================

    def _build_prompt(
        self,
        text: str,
    ) -> str:

        return f"""
You are an expert legal-document information extraction system.

Extract the required fields from the LSR / Legal Scrutiny Report
document provided below.

IMPORTANT:
- Return ONLY one valid JSON object.
- Do NOT use Markdown.
- Do NOT use ```json.
- Do NOT add explanations.
- Do NOT add comments.
- Do NOT truncate the JSON.
- Use null when a field cannot be confidently found.
- Never invent information.
- Preserve names, dates, numbers and document identifiers exactly
  as they appear in the document.

REQUIRED JSON STRUCTURE:

{{
    "lsr_date": null,
    "company_name": null,
    "applicant_name": null,
    "co_applicant_name": null,
    "property_owner": null,
    "application_number": null,
    "property_description": null
}}

FIELD EXTRACTION RULES:

1. lsr_date

Find the date associated with the Legal Scrutiny Report /
legal opinion.

Look especially near:
- "Dated:"
- "Date:"
- the beginning/header of the legal opinion.

Return only the date.

Example:
"27-07-2026"

Do not confuse it with:
- sale deed dates
- document dates
- registration dates
- survey dates.

------------------------------------------------------------

2. company_name

Find the organization/company addressed in the legal opinion.

Usually it appears immediately after:

"To,"

Return the complete company name.

Example:

"VASTU HOUSING FINANCE CORPORATION LIMITED."

------------------------------------------------------------

3. applicant_name

Find:

"Name of the Applicant / Borrower/s:"

Return ONLY the applicant/borrower name.

Do not include:
- co-applicants
- property owners
- relationship information
- addresses.

------------------------------------------------------------

4. co_applicant_name

Find:

"Name of the Co - Applicant / Borrower/s:"

or similar variations such as:

"Name of the Co-Applicant / Borrower/s:"

Return all co-applicant names.

If there are multiple co-applicants, preserve all names.

If there is no co-applicant, return null.

------------------------------------------------------------

5. property_owner

Find:

"Name of the Property Owner:"

Return ONLY the property owner's name.

Do not include:
- applicant names
- co-applicant names
- addresses
- relationship descriptions unless they are part of the owner's stated name.

------------------------------------------------------------

6. application_number

Find the value associated with:

"APP. NO."

Also consider variations such as:

"APP NO"
"APPLICATION NO"
"APPLICATION NUMBER"
"Application No."

Return the identifier exactly as written.

Do not confuse it with:
- document number
- survey number
- registration number
- loan account number.

------------------------------------------------------------

7. property_description

Extract the COMPLETE property description.

Look for sections such as:

"Property Address and Description"

or:

"Property Description"

Include ALL relevant information such as:

- property address
- village
- taluk
- district
- survey numbers
- subdivision numbers
- R.S. numbers
- T.S. numbers
- Ward
- Block
- extent
- measurements
- flat number
- floor
- building name
- undivided share
- boundaries
- North boundary
- South boundary
- East boundary
- West boundary

Preserve the original wording as much as possible.

Do not summarize the property description.

Do not omit survey numbers.

Do not omit taluk, district, ward or block information.

------------------------------------------------------------

IMPORTANT DIFFERENCE:

"application_number" is the application identifier.

"property_description" contains the property information.

Do NOT put property survey numbers into application_number.

------------------------------------------------------------

DOCUMENT:

{text}
""".strip()

    # ============================================================
    # RESPONSE PARSER
    # ============================================================

    def _parse_response(
        self,
        response: str,
    ) -> dict:

        if not response or not response.strip():

            raise RuntimeError(
                "FreeLLM returned an empty response."
            )

        json_text = self._extract_json_block(
            response
        )

        try:

            data = json.loads(
                json_text
            )

        except json.JSONDecodeError as exc:

            print(
                "\n❌ Invalid JSON from FreeLLM:"
            )

            print(response)

            raise RuntimeError(
                f"FreeLLM returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):

            raise RuntimeError(
                "FreeLLM response must be a JSON object."
            )

        # --------------------------------------------------------
        # Normalize to required fields
        # --------------------------------------------------------

        result = {}

        for field in REQUIRED_FIELDS:

            value = data.get(
                field,
                None,
            )

            if isinstance(
                value,
                str,
            ):

                value = value.strip()

                if not value:
                    value = None

            result[field] = value

        return result

    # ============================================================
    # JSON EXTRACTION
    # ============================================================

    def _extract_json_block(
        self,
        response: str,
    ) -> str:

        response = response.strip()

        # --------------------------------------------------------
        # Remove Markdown fences
        # --------------------------------------------------------

        response = re.sub(
            r"```json\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"```\s*",
            "",
            response,
        )

        response = response.strip()

        # --------------------------------------------------------
        # Direct JSON
        # --------------------------------------------------------

        if response.startswith("{"):

            end = response.rfind("}")

            if end != -1:

                return response[: end + 1]

        # --------------------------------------------------------
        # JSON embedded inside explanation
        # --------------------------------------------------------

        start = response.find("{")
        end = response.rfind("}")

        if (
            start != -1
            and end != -1
            and end > start
        ):

            return response[
                start : end + 1
            ]

        raise RuntimeError(
            "No JSON object found in FreeLLM response."
        )

    # ============================================================
    # MISSING FIELD RECOVERY
    # ============================================================

    def _recover_missing_fields(
        self,
        text: str,
        result: dict,
        missing_fields: list,
    ) -> dict:

        """
        Recover simple labelled fields from OCR text.

        This is NOT the primary extraction method.
        It is only a fallback when the LLM misses
        an explicitly labelled field.
        """

        for field in missing_fields:

            try:

                value = self._extract_labelled_value(
                    text,
                    field,
                )

                if value:
                    result[field] = value

            except Exception as exc:

                print(
                    f"⚠️ Recovery failed for "
                    f"{field}: {exc}"
                )

        return result

    # ============================================================
    # LABELLED VALUE EXTRACTION
    # ============================================================

    def _extract_labelled_value(
        self,
        text: str,
        field: str,
    ) -> Optional[str]:

        labels = {

            "company_name": [
                r"To\s*[,:\-]?\s*",
            ],

            "applicant_name": [
                r"Name\s+of\s+the\s+Applicant\s*/\s*Borrower(?:/s)?\s*[:\-]?\s*",
            ],

            "co_applicant_name": [
                r"Name\s+of\s+the\s+Co\s*[-]?\s*Applicant\s*/\s*Borrower(?:/s)?\s*[:\-]?\s*",
            ],

            "property_owner": [
                r"Name\s+of\s+the\s+Property\s+Owner\s*[:\-]?\s*",
            ],

            "application_number": [
                r"APP\.?\s*NO\.?\s*[:\-]?\s*",
                r"APPLICATION\s+NO\.?\s*[:\-]?\s*",
                r"APPLICATION\s+NUMBER\s*[:\-]?\s*",
            ],

            "lsr_date": [
                r"Dated\s*[:\-]?\s*",
                r"Date\s*[:\-]?\s*",
            ],

            "property_description": [
                r"Property\s+Address\s+and\s+Description\s*[:\-]?\s*",
                r"Property\s+Description\s*[:\-]?\s*",
            ],
        }

        field_labels = labels.get(
            field,
            [],
        )

        for label_pattern in field_labels:

            pattern = re.compile(
                label_pattern
                + r"([^\r\n]+)",
                flags=re.IGNORECASE,
            )

            match = pattern.search(
                text
            )

            if not match:
                continue

            value = match.group(1).strip()

            if value:
                return value

        return None