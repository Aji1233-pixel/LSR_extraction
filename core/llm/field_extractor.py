import json
import re
import time
from typing import Optional

from core.config.fields import REQUIRED_FIELDS
from .freellm_client import FreeLLMClient


class FieldExtractor:
    """
    Hybrid field extractor for LSR documents.

    Extraction strategy:
    1. Extract simple fields deterministically using labels.
    2. Identify fields that are still missing.
    3. Use FreeLLMClient only for missing fields.
    4. Parse and repair LLM JSON when necessary.
    5. Return only REQUIRED_FIELDS.
    """

    FIELD_ALIASES = {
        "lsr_date": [
            "LSR Date",
            "Date of Report",
            "Report Date",
            "Valuation Date",
            "Date",
            "Dated",
        ],
        "company_name": [
            "Company Name",
            "Lender Name",
            "Bank Name",
            "Financial Institution",
            "Company",
            "Lender",
            "Bank",
        ],
        "applicant_name": [
            "Applicant Name",
            "Borrower Name",
            "Applicant",
            "Proposed Borrower",
            "Borrower",
        ],
        "co_applicant_name": [
            "Co-Applicant Name",
            "Co-Applicant",
            "Co Applicant",
            "Co-Borrower",
            "Co Borrower",
            "Joint Applicant",
        ],
        "property_owner": [
            "Property Owner",
            "Owner Name",
            "Title Holder",
            "Owner",
        ],
        "application_number": [
            "Application Number",
            "Application No",
            "File No",
            "Reference No",
            "App No",
            "App. No.",
        ],
        "property_description": [
            "Property Description",
            "Description of Property",
            "Property Details",
        ],
    }

    def __init__(self, llm_client: Optional[FreeLLMClient] = None):
        """
        Initialize the field extractor.

        If an LLM client is supplied, use it.
        Otherwise create a FreeLLMClient automatically.
        """
        self.llm = llm_client or FreeLLMClient()

    # ============================================================
    # MAIN EXTRACTION
    # ============================================================

    def extract_fields(self, text: str) -> dict:
        """
        Extract required fields from OCR/document text.
        """

        if not text or not text.strip():
            raise ValueError("Document text cannot be empty.")

        print("\n" + "=" * 60)
        print("HYBRID FIELD EXTRACTION STARTED")
        print("=" * 60)

        print(f"Input characters: {len(text)}")
        print(f"Input words: {len(text.split())}")

        start_time = time.perf_counter()

        # --------------------------------------------------------
        # STEP 1: LABEL-BASED EXTRACTION
        # --------------------------------------------------------

        label_start = time.perf_counter()

        result = self._extract_by_labels(text)

        label_time = time.perf_counter() - label_start

        print(
            f"Label-based extraction: "
            f"{label_time:.2f} seconds"
        )

        print("\n========== LABEL EXTRACTION ==========")

        for field, value in result.items():
            print(f"{field}: {value}")

        print("======================================")

        # --------------------------------------------------------
        # STEP 2: FIND MISSING FIELDS
        # --------------------------------------------------------

        missing_fields = [
            field
            for field in REQUIRED_FIELDS
            if self._is_missing(result.get(field))
        ]

        print(
            f"\nMissing fields after label extraction: "
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
                f"FreeLLM fallback: "
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
            f"\nTotal field extraction: "
            f"{total_time:.2f} seconds"
        )

        print("=" * 60)

        return final_result

    # ============================================================
    # LABEL-BASED EXTRACTION
    # ============================================================

    def _extract_by_labels(self, text: str) -> dict:

        lines = self._prepare_lines(text)

        result = {
            field: None
            for field in REQUIRED_FIELDS
        }

        # --------------------------------------------------------
        # LSR DATE
        # --------------------------------------------------------

        result["lsr_date"] = self._find_value_after_labels(
            lines,
            [
                "lsr date",
                "dated",
                "date of report",
                "report date",
                "valuation date",
                "date",
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
                "applicant / borrower",
                "applicant name",
                "borrower name",
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
                "co-borrower name",
                "co borrower name",
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
                "owner name",
                "title holder",
                "owner",
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
                "file no",
                "reference no",
            ],
        )

        # --------------------------------------------------------
        # PROPERTY DESCRIPTION
        #
        # Deliberately left for FreeLLM because it is generally
        # long and unstructured.
        # --------------------------------------------------------

        return result

    # ============================================================
    # COMPANY NAME
    # ============================================================

    def _find_company_name(
        self,
        lines: list[str],
    ) -> Optional[str]:

        # --------------------------------------------------------
        # First: look for "To,"
        # --------------------------------------------------------

        for index, line in enumerate(lines):

            normalized = self._normalize(line)

            if normalized in {"to,", "to"}:

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

        # --------------------------------------------------------
        # Second: search for company indicators
        # --------------------------------------------------------

        company_words = [
            "limited",
            "ltd",
            "finance",
            "housing finance",
            "bank",
            "corporation",
            "private limited",
            "pvt ltd",
        ]

        for line in lines:

            lowered = line.lower()

            if any(word in lowered for word in company_words):

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
                # CASE 1
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
                # CASE 2
                #
                # Label: Value
                # ------------------------------------------------

                if normalized_line.startswith(label):

                    remaining = line.strip()[len(label):].strip()

                    remaining = remaining.lstrip(
                        ":：-–"
                    )

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

    def _looks_like_label(
        self,
        value: str,
    ) -> bool:

        normalized = self._normalize(value)

        known_labels = [
            "name of the applicant",
            "name of applicant",
            "name of the co applicant",
            "name of the co-applicant",
            "property owner",
            "property owner name",
            "application number",
            "application no",
            "app no",
            "app. no",
            "property address",
            "property description",
            "name of the company",
            "company name",
            "applicant name",
            "borrower name",
            "co-applicant name",
            "co applicant name",
            "owner name",
            "title holder",
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
        print("======================================")

        # --------------------------------------------------------
        # Retry empty LLM responses
        # --------------------------------------------------------

        max_retries = 3
        response = None

        for attempt in range(max_retries):

            try:
                response = self.llm.generate(prompt)
            except Exception as exc:
                print(
                    f"FreeLLM error "
                    f"(attempt {attempt + 1}/{max_retries}): "
                    f"{exc}"
                )
                response = None

            if response and response.strip():
                break

            print(
                f"LLM returned empty response "
                f"(attempt {attempt + 1}/{max_retries})"
            )

            if attempt < max_retries - 1:
                time.sleep(1)

        # --------------------------------------------------------
        # If LLM completely fails
        # --------------------------------------------------------

        if not response or not response.strip():

            print(
                "LLM failed after retries. "
                "Using regex fallback."
            )

            return self._fallback_extraction(text)

        # --------------------------------------------------------
        # Parse LLM response
        # --------------------------------------------------------

        try:

            result = self._parse_llm_response(
                response
            )

        except (RuntimeError, json.JSONDecodeError) as exc:

            print(
                f"LLM JSON parsing failed: {exc}"
            )

            print(
                "Using regex fallback."
            )

            return self._fallback_extraction(text)

        # --------------------------------------------------------
        # If LLM extracted almost nothing,
        # use regex as supplementary extraction.
        # --------------------------------------------------------

        non_null_count = sum(
            1
            for value in result.values()
            if not self._is_missing(value)
        )

        if non_null_count < 1:

            print(
                "LLM extracted no useful fields. "
                "Using regex fallback."
            )

            return self._fallback_extraction(text)

        return result

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

RULES:

1. Extract values only when explicitly present.
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
The date associated with the LSR/legal opinion.

company_name:
The organization/company/lender/financial institution
addressed in the legal opinion.

applicant_name:
Only the primary applicant/borrower name.

co_applicant_name:
Only the co-applicant/co-borrower name or names.

property_owner:
Only the property owner/title holder name or names.

application_number:
The application number, APP NO., file number,
or equivalent reference number.

property_description:
The complete property address and description including
survey numbers, extent, measurements and boundaries.

REQUIRED JSON FORMAT:

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

        # --------------------------------------------------------
        # Remove Markdown code fences
        # --------------------------------------------------------

        if cleaned.startswith("```"):

            lines = cleaned.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        # --------------------------------------------------------
        # Direct JSON parse
        # --------------------------------------------------------

        try:

            data = json.loads(cleaned)

            return self._extract_fields(data)

        except json.JSONDecodeError:
            pass

        # --------------------------------------------------------
        # JSON repair
        # --------------------------------------------------------

        repaired = self._attempt_json_repair(
            cleaned
        )

        if repaired is not None:

            return self._extract_fields(
                repaired
            )

        raise RuntimeError(
            "LLM returned invalid JSON "
            "that could not be repaired."
        )

    # ============================================================
    # JSON REPAIR
    # ============================================================

    def _attempt_json_repair(
        self,
        text: str,
    ) -> Optional[dict]:

        # --------------------------------------------------------
        # Strategy 1:
        # Remove trailing commas and close structures.
        # --------------------------------------------------------

        try:

            fixed = text.rstrip()

            fixed = re.sub(
                r",\s*([}\]])",
                r"\1",
                fixed,
            )

            open_braces = max(
                0,
                fixed.count("{") - fixed.count("}"),
            )

            open_brackets = max(
                0,
                fixed.count("[") - fixed.count("]"),
            )

            fixed += "]" * open_brackets
            fixed += "}" * open_braces

            data = json.loads(fixed)

            print(
                "[OK] Repaired JSON "
                "(trailing commas / brackets)"
            )

            return data

        except json.JSONDecodeError:
            pass

        # --------------------------------------------------------
        # Strategy 2:
        # Recover individual fields using regex.
        # --------------------------------------------------------

        try:

            return self._extract_from_malformed_json(
                text
            )

        except Exception:
            pass

        return None

    # ============================================================
    # MALFORMED JSON FIELD EXTRACTION
    # ============================================================

    def _extract_from_malformed_json(
        self,
        text: str,
    ) -> dict:

        result = {
            field: None
            for field in REQUIRED_FIELDS
        }

        for field in REQUIRED_FIELDS:

            pattern = (
                rf'"{re.escape(field)}"'
                r'\s*:\s*"((?:[^"\\]|\\.)*)"'
            )

            match = re.search(
                pattern,
                text,
            )

            if match:

                value = match.group(1)

                value = (
                    value
                    .replace('\\"', '"')
                    .replace("\\n", "\n")
                    .replace("\\t", "\t")
                )

                result[field] = value

                continue

            # ----------------------------------------------------
            # Check for null
            # ----------------------------------------------------

            null_pattern = (
                rf'"{re.escape(field)}"'
                r"\s*:\s*null"
            )

            if re.search(
                null_pattern,
                text,
            ):
                result[field] = None

        non_null = sum(
            1
            for value in result.values()
            if not self._is_missing(value)
        )

        if non_null > 0:

            print(
                f"[OK] Extracted {non_null} fields "
                "from malformed JSON"
            )

            return result

        raise ValueError(
            "Could not extract any fields "
            "from malformed JSON."
        )

    # ============================================================
    # EXTRACT REQUIRED FIELDS
    # ============================================================

    def _extract_fields(
        self,
        data: dict,
    ) -> dict:

        if not isinstance(data, dict):

            raise RuntimeError(
                "FreeLLM response must be a JSON object."
            )

        result = {
            field: data.get(field)
            for field in REQUIRED_FIELDS
        }

        return result

    # ============================================================
    # REGEX FALLBACK
    # ============================================================

    def _fallback_extraction(
        self,
        text: str,
    ) -> dict:

        result = {
            field: None
            for field in REQUIRED_FIELDS
        }

        # --------------------------------------------------------
        # Generic field extractor
        # --------------------------------------------------------

        def extract_field(
            aliases,
            pattern_suffix=r":\s*([^\n]+)",
        ):

            for alias in aliases:

                escaped_alias = re.escape(alias)

                pattern = (
                    escaped_alias
                    + pattern_suffix
                )

                match = re.search(
                    pattern,
                    text,
                    re.IGNORECASE,
                )

                if match:

                    return self._clean_value(
                        match.group(1)
                    )

            return None

        # --------------------------------------------------------
        # Date extractor
        # --------------------------------------------------------

        def extract_date(aliases):

            for alias in aliases:

                escaped_alias = re.escape(alias)

                pattern = (
                    escaped_alias
                    + r"[:]?\s*"
                    r"(\d{1,2}"
                    r"[/\-\.]"
                    r"\d{1,2}"
                    r"[/\-\.]"
                    r"\d{2,4})"
                )

                match = re.search(
                    pattern,
                    text,
                    re.IGNORECASE,
                )

                if match:
                    return match.group(1)

            return None

        # --------------------------------------------------------
        # Basic fields
        # --------------------------------------------------------

        result["lsr_date"] = extract_date(
            self.FIELD_ALIASES["lsr_date"]
        )

        result["company_name"] = extract_field(
            self.FIELD_ALIASES["company_name"]
        )

        result["applicant_name"] = extract_field(
            self.FIELD_ALIASES["applicant_name"]
        )

        result["co_applicant_name"] = extract_field(
            self.FIELD_ALIASES["co_applicant_name"]
        )

        result["property_owner"] = extract_field(
            self.FIELD_ALIASES["property_owner"]
        )

        result["application_number"] = extract_field(
            self.FIELD_ALIASES["application_number"]
        )

        # --------------------------------------------------------
        # Property description
        # --------------------------------------------------------

        desc_start_patterns = [
            r"Property Description:",
            r"Description of Property:",
            r"Property Details:",
            r"PART\s*-\s*I\s*:\s*DESCRIPTION\s+OF\s+THE\s+PROPERTY",
        ]

        desc_end_patterns = [
            r"DOCUMENTS\s+PRIOR\s+TO\s+DISBURSAL",
            r"PART\s*-\s*II",
            r"BOUNDARIES",
            r"LIST\s+OF\s+DOCUMENTS",
            r"FLOW\s+OF\s+TITLE",
        ]

        for start_pattern in desc_start_patterns:

            if result.get("property_description"):
                break

            for end_pattern in desc_end_patterns:

                pattern = (
                    start_pattern
                    + r"(.*?)"
                    + end_pattern
                )

                match = re.search(
                    pattern,
                    text,
                    re.IGNORECASE | re.DOTALL,
                )

                if match:

                    result["property_description"] = (
                        self._clean_value(
                            match.group(1)
                        )
                    )

                    break

        return result

    # ============================================================
    # TEXT HELPERS
    # ============================================================

    @staticmethod
    def _prepare_lines(
        text: str,
    ) -> list[str]:

        lines = []

        for line in text.splitlines():

            cleaned = " ".join(
                line.strip().split()
            )

            if cleaned:
                lines.append(cleaned)

        return lines

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:

        value = " ".join(
            value.lower().strip().split()
        )

        replacements = {
            "–": "-",
            "—": "-",
            "：": ":",
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        value = value.replace(
            " - ",
            "-",
        )

        return value

    @staticmethod
    def _clean_value(
        value: str,
    ) -> Optional[str]:

        if value is None:
            return None

        if not isinstance(value, str):
            return value

        value = " ".join(
            value.strip().split()
        )

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
    def _is_missing(
        value,
    ) -> bool:

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