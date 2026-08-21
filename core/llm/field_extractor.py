import json
import time
from typing import Optional

from core.config.fields import REQUIRED_FIELDS
from .freellm_client import FreeLLMClient


class FieldExtractor:
    """
    Hybrid basic-field extractor.

    Strategy:
    1. Try deterministic label-based extraction first.
    2. Use FreeLLM only for fields that could not be extracted.
    3. Property description is extracted by FreeLLM because it is
       a long and unstructured section.
    """

    def __init__(self, llm_client: Optional[FreeLLMClient] = None):
        self.llm = llm_client or FreeLLMClient()

    # ============================================================
    # MAIN EXTRACTION
    # ============================================================

    def extract_fields(self, text: str) -> dict:

        if not text or not text.strip():
            raise ValueError("Document text cannot be empty.")

        print("\n" + "=" * 50)
        print("HYBRID FIELD EXTRACTION STARTED")
        print("=" * 50)

        print(f"📝 Input characters: {len(text)}")
        print(f"📝 Input words: {len(text.split())}")

        start_time = time.perf_counter()

        # --------------------------------------------------------
        # STEP 1: LABEL-BASED EXTRACTION
        # --------------------------------------------------------

        label_start = time.perf_counter()

        result = self._extract_by_labels(text)

        label_time = time.perf_counter() - label_start

        print(
            f"⏱️ Label-based extraction: "
            f"{label_time:.2f} seconds"
        )

        print("\n========== LABEL EXTRACTION ==========")

        for field, value in result.items():
            print(f"{field}: {value}")

        print("======================================\n")

        # --------------------------------------------------------
        # STEP 2: DETERMINE MISSING FIELDS
        # --------------------------------------------------------

        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if self._is_missing(result.get(field))
        ]

        print(
            f"🔎 Missing fields after label extraction: "
            f"{missing_fields}"
        )

        # --------------------------------------------------------
        # STEP 3: FREE LLM FALLBACK
        # --------------------------------------------------------

        if missing_fields:

            llm_start = time.perf_counter()

            fallback_result = self._extract_with_llm(
                text=text,
                missing_fields=missing_fields,
            )

            llm_time = time.perf_counter() - llm_start

            print(
                f"⏱️ FreeLLM fallback: "
                f"{llm_time:.2f} seconds"
            )

            # ----------------------------------------------------
            # MERGE
            # ----------------------------------------------------

            for field in missing_fields:

                llm_value = fallback_result.get(field)

                if not self._is_missing(llm_value):
                    result[field] = llm_value

        # --------------------------------------------------------
        # STEP 4: FINAL RESULT
        # --------------------------------------------------------

        final_result = {
            field: result.get(field)
            for field in REQUIRED_FIELDS
        }

        total_time = time.perf_counter() - start_time

        print("\n========== FINAL FIELD RESULT ==========")

        for field, value in final_result.items():
            print(f"{field}: {value}")

        print(
            f"\n⏱️ Total field extraction: "
            f"{total_time:.2f} seconds"
        )

        print("=" * 50)

        return final_result

    # ============================================================
    # LABEL-BASED EXTRACTION
    # ============================================================

    def _extract_by_labels(self, text: str) -> dict:

        lines = self._prepare_lines(text)

        result = {
            "lsr_date": None,
            "company_name": None,
            "applicant_name": None,
            "co_applicant_name": None,
            "property_owner": None,
            "application_number": None,
            "property_description": None,
        }

        # --------------------------------------------------------
        # LSR DATE
        # --------------------------------------------------------

        result["lsr_date"] = self._find_value_after_labels(
            lines,
            [
                "dated",
                "date",
                "lsr date",
            ],
        )

        # --------------------------------------------------------
        # COMPANY NAME
        # --------------------------------------------------------

        result["company_name"] = self._find_company_name(lines)

        # --------------------------------------------------------
        # APPLICANT
        # --------------------------------------------------------

        result["applicant_name"] = self._find_value_after_labels(
            lines,
            [
                "name of the applicant / borrower/s",
                "name of the applicant / borrower",
                "name of applicant / borrower/s",
                "name of applicant / borrower",
                "applicant / borrower/s",
                "applicant name",
            ],
        )

        # --------------------------------------------------------
        # CO-APPLICANT
        # --------------------------------------------------------

        result["co_applicant_name"] = self._find_value_after_labels(
            lines,
            [
                "name of the co - applicant / borrower/s",
                "name of the co-applicant / borrower/s",
                "name of the co applicant / borrower/s",
                "name of the co-applicant / borrower",
                "name of co-applicant / borrower/s",
                "co-applicant name",
                "co applicant name",
            ],
        )

        # --------------------------------------------------------
        # PROPERTY OWNER
        # --------------------------------------------------------

        result["property_owner"] = self._find_value_after_labels(
            lines,
            [
                "name of the property owner",
                "property owner name",
                "property owner",
            ],
        )

        # --------------------------------------------------------
        # APPLICATION NUMBER
        # --------------------------------------------------------

        result["application_number"] = self._find_value_after_labels(
            lines,
            [
                "app. no.",
                "app.no.",
                "app no.",
                "app no",
                "application no.",
                "application no",
                "application number",
            ],
        )

        # --------------------------------------------------------
        # PROPERTY DESCRIPTION
        #
        # We deliberately leave this to FreeLLM.
        # It is generally a long, unstructured section.
        # --------------------------------------------------------

        return result

    # ============================================================
    # COMPANY NAME
    # ============================================================

    def _find_company_name(self, lines: list[str]) -> Optional[str]:

        # First look for "To,"
        for index, line in enumerate(lines):

            normalized = self._normalize(line)

            if normalized == "to," or normalized == "to":

                # Usually the company is on the next meaningful line.
                value = self._next_meaningful_line(
                    lines,
                    index,
                )

                if value and not self._looks_like_label(value):
                    return self._clean_value(value)

            if normalized.startswith("to,"):

                value = line.split(",", 1)[1].strip()

                if value:
                    return self._clean_value(value)

        # Fallback: search for common company indicators.
        company_words = [
            "limited",
            "ltd",
            "finance",
            "housing finance",
            "bank",
        ]

        for line in lines:

            lowered = line.lower()

            if any(word in lowered for word in company_words):

                # Avoid obvious unrelated sentences.
                if len(line.split()) <= 15:
                    return self._clean_value(line)

        return None

    # ============================================================
    # GENERIC LABEL EXTRACTION
    # ============================================================

    def _find_value_after_labels(
        self,
        lines: list[str],
        labels: list[str],
    ) -> Optional[str]:

        normalized_labels = [
            self._normalize(label)
            for label in labels
        ]

        for index, line in enumerate(lines):

            normalized_line = self._normalize(line)

            for label in normalized_labels:

                # ------------------------------------------------
                # Case 1:
                #
                # Label:
                # Value
                # ------------------------------------------------

                if normalized_line == label:

                    value = self._next_meaningful_line(
                        lines,
                        index,
                    )

                    if value and not self._looks_like_label(value):
                        return self._clean_value(value)

                # ------------------------------------------------
                # Case 2:
                #
                # Label: Value
                # ------------------------------------------------

                if normalized_line.startswith(label):

                    remaining = line.strip()[len(label):].strip()

                    # Remove common separators.
                    remaining = remaining.lstrip(":：-–")

                    if remaining.strip():
                        return self._clean_value(
                            remaining
                        )

        return None

    # ============================================================
    # NEXT MEANINGFUL LINE
    # ============================================================

    def _next_meaningful_line(
        self,
        lines: list[str],
        current_index: int,
    ) -> Optional[str]:

        for index in range(
            current_index + 1,
            min(current_index + 5, len(lines)),
        ):

            candidate = lines[index].strip()

            if not candidate:
                continue

            if self._looks_like_label(candidate):
                return None

            return candidate

        return None

    # ============================================================
    # LABEL DETECTION
    # ============================================================

    def _looks_like_label(self, value: str) -> bool:

        normalized = self._normalize(value)

        known_labels = [
            "name of the applicant",
            "name of applicant",
            "name of the co applicant",
            "name of the co-applicant",
            "name of the property owner",
            "property owner",
            "application number",
            "application no",
            "app no",
            "app. no",
            "property address",
            "property description",
            "name of the company",
            "company name",
        ]

        return any(
            normalized.startswith(label)
            for label in known_labels
        )

    # ============================================================
    # FREE LLM FALLBACK
    # ============================================================

    def _extract_with_llm(
        self,
        text: str,
        missing_fields: list[str],
    ) -> dict:

        prompt = self._build_fallback_prompt(
            text=text,
            missing_fields=missing_fields,
        )

        print("\n========== FREELLM FALLBACK ==========")
        print(
            f"Fields requested: {missing_fields}"
        )
        print("======================================\n")

        response = self.llm.generate(prompt)

        return self._parse_llm_response(response)

    # ============================================================
    # FALLBACK PROMPT
    # ============================================================

    def _build_fallback_prompt(
        self,
        text: str,
        missing_fields: list[str],
    ) -> str:

        requested_fields = ", ".join(
            missing_fields
        )

        return f"""
Extract ONLY these missing fields from the legal property document:

{requested_fields}

Return ONLY valid JSON.

Rules:

1. Extract values only when they are explicitly present.
2. Do not guess.
3. Do not infer.
4. Preserve names exactly as written.
5. Preserve numbers exactly as written.
6. If a field cannot be found, return null.
7. Do not move a value from one field to another.
8. Do not include explanations.
9. Return JSON only.

FIELD DEFINITIONS:

lsr_date:
The date associated with the LSR/legal opinion, usually near the
beginning of the document.

company_name:
The organization/company addressed in the legal opinion.

applicant_name:
Only the applicant/borrower name.

co_applicant_name:
Only the co-applicant/borrower name or names.

property_owner:
Only the property owner name or names.

application_number:
The application number, APP NO., or equivalent reference.

property_description:
The complete property address and description including survey
numbers, extent, measurements and boundaries.

Required JSON:

{{
    "lsr_date": null,
    "company_name": null,
    "applicant_name": null,
    "co_applicant_name": null,
    "property_owner": null,
    "application_number": null,
    "property_description": null
}}

DOCUMENT TEXT:

{text}
""".strip()

    # ============================================================
    # JSON PARSING
    # ============================================================

    def _parse_llm_response(
        self,
        response: str,
    ) -> dict:

        if not response or not response.strip():
            raise RuntimeError(
                "FreeLLM returned an empty response."
            )

        cleaned = response.strip()

        # Remove Markdown JSON fences if present.
        if cleaned.startswith("```"):

            lines = cleaned.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        try:

            data = json.loads(cleaned)

        except json.JSONDecodeError as exc:

            print(
                "\n========== INVALID FREELLM JSON =========="
            )
            print(cleaned)
            print(
                "==========================================\n"
            )

            raise RuntimeError(
                f"FreeLLM returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "FreeLLM response must be a JSON object."
            )

        return {
            field: data.get(field)
            for field in REQUIRED_FIELDS
        }

    # ============================================================
    # TEXT HELPERS
    # ============================================================

    @staticmethod
    def _prepare_lines(text: str) -> list[str]:

        lines = []

        for line in text.splitlines():

            cleaned = " ".join(
                line.strip().split()
            )

            if cleaned:
                lines.append(cleaned)

        return lines

    @staticmethod
    def _normalize(value: str) -> str:

        value = " ".join(
            value.lower().strip().split()
        )

        # Normalize common OCR variations.
        replacements = {
            "–": "-",
            "—": "-",
            "：": ":",
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        value = value.replace(
            " - ",
            "-"
        )

        return value

    @staticmethod
    def _clean_value(value: str) -> Optional[str]:

        if not value:
            return None

        value = " ".join(
            value.strip().split()
        )

        # Common OCR/LLM missing-value responses.
        missing_values = {
            "",
            "nil",
            "n/a",
            "na",
            "not available",
            "not found",
            "none",
            "null",
            "-",
        }

        if value.lower() in missing_values:
            return None

        return value

    @staticmethod
    def _is_missing(value) -> bool:

        if value is None:
            return True

        if isinstance(value, str):

            return value.strip().lower() in {
                "",
                "null",
                "none",
                "nil",
                "n/a",
                "na",
                "not found",
                "not available",
                "-",
            }

        return False