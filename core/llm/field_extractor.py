import json
import time
import re
from core.config.fields import REQUIRED_FIELDS
from .freellm_client import FreeLLMClient


class FieldExtractor:
    """Extract required fields from document text."""

    # Field aliases for flexible label matching across different document formats
    FIELD_ALIASES = {
        "lsr_date": [
            "LSR Date",
            "Date of Report",
            "Report Date",
            "Valuation Date",
            "LSR Date:",
            "Date:",
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
            "Applicant Name:",
            "Borrower Name:",
        ],
        "co_applicant_name": [
            "Co-Applicant Name",
            "Co-Applicant",
            "Co-Borrower",
            "Joint Applicant",
            "Co-Applicant Name:",
            "Co-Borrower Name:",
        ],
        "property_owner": [
            "Property Owner",
            "Owner Name",
            "Title Holder",
            "Property Owner:",
            "Owner:",
        ],
        "application_number": [
            "Application Number",
            "Application No",
            "File No",
            "Reference No",
            "App No",
            "Application Number:",
            "App. No.",
        ],
        "property_description": [
            "Property Description",
            "Description of Property",
            "Property Details",
            "Property Description:",
        ],
    }

    def __init__(self, llm_client):
        self.ollama = llm_client

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
        # Ollama (with retry logic for empty responses and LLM failures)
        # -------------------------------

        ollama_start = time.perf_counter()

        max_retries = 3
        response = None

        for attempt in range(max_retries):
            try:
                response = self.ollama.generate(prompt)
                if response and response.strip():
                    break
                print(f"⚠️ LLM returned empty response (attempt {attempt + 1}/{max_retries}), retrying...")
            except RuntimeError as exc:
                print(f"⚠️ LLM runtime error (attempt {attempt + 1}/{max_retries}): {exc}")
                if attempt == max_retries - 1:
                    print("⚠️ LLM failed after retries, using fallback regex extraction...")
                    return self._fallback_extraction(text)
            # Exponential backoff: 2s, 4s, 8s...
            wait_time = min(2 ** (attempt + 1), 30)
            time.sleep(wait_time)

        if not response or not response.strip():
            print("⚠️ LLM failed after retries, using fallback regex extraction...")
            return self._fallback_extraction(text)

        ollama_time = time.perf_counter() - ollama_start

        print(
            f"⏱️ LLM extraction: "
            f"{ollama_time:.2f} seconds"
        )

        # -------------------------------
        # JSON parsing (with fallback to regex)
        # -------------------------------

        parse_start = time.perf_counter()

        result = None

        try:
            result = self._parse_response(response)

            parse_time = time.perf_counter() - parse_start

            print(
                f"⏱️ JSON parsing: "
                f"{parse_time:.2f} seconds"
            )

            print("=" * 50)

        except (RuntimeError, json.JSONDecodeError) as exc:
            print(f"⚠️ JSON parsing failed: {exc}")
            print("   Falling back to regex extraction...")
            result = None

        # If parsing failed or LLM returned mostly nulls, use fallback
        if result is None:
            print("⚠️ Using fallback regex extraction...")
            return self._fallback_extraction(text)

        non_null_count = sum(1 for v in result.values() if v not in [None, "", [], {}])
        if non_null_count < 3:  # If less than 3 fields extracted, use fallback
            print(f"⚠️ LLM extracted only {non_null_count} fields, using fallback regex extraction...")
            fallback_result = self._fallback_extraction(text)
            # Merge: prefer LLM values, fallback for missing ones
            for key in REQUIRED_FIELDS:
                if result.get(key) in [None, "", [], {}] and fallback_result.get(key) not in [None, "", [], {}]:
                    result[key] = fallback_result[key]
                    print(f"   Fallback filled: {key} = {fallback_result[key]}")

        return result

    def _fallback_extraction(self, text: str) -> dict:
        """Fallback regex-based extraction when LLM fails."""
        result = {field: None for field in REQUIRED_FIELDS}

        # Helper to find field value using multiple aliases
        def extract_field(aliases, pattern_suffix=r':\s*([^\n]+)', flags=re.IGNORECASE):
            for alias in aliases:
                # Escape special regex characters in alias
                escaped_alias = re.escape(alias)
                pattern = escaped_alias + pattern_suffix
                match = re.search(pattern, text, flags)
                if match:
                    return match.group(1).strip()
            return None

        # Helper to find date with multiple aliases
        def extract_date(aliases):
            for alias in aliases:
                escaped_alias = re.escape(alias)
                # Match various date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, etc.
                pattern = escaped_alias + r'[:]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
            return None

        # LSR Date - use aliases with date pattern
        result["lsr_date"] = extract_date(self.FIELD_ALIASES["lsr_date"])

        # Company Name
        result["company_name"] = extract_field(self.FIELD_ALIASES["company_name"])

        # Applicant Name
        result["applicant_name"] = extract_field(self.FIELD_ALIASES["applicant_name"])

        # Co-Applicant Name
        result["co_applicant_name"] = extract_field(self.FIELD_ALIASES["co_applicant_name"])

        # Property Owner
        result["property_owner"] = extract_field(self.FIELD_ALIASES["property_owner"])

        # Application Number
        result["application_number"] = extract_field(self.FIELD_ALIASES["application_number"])

        # Property Description - more flexible extraction
        # Try multiple start markers and end markers
        desc_start_patterns = [
            r'Property Description:',
            r'Description of Property:',
            r'Property Details:',
            r'PART\s*-\s*I\s*:\s*DESCRIPTION\s+OF\s+THE\s+PROPERTY',
        ]
        desc_end_patterns = [
            r'DOCUMENTS\s+PRIOR\s+TO\s+DISBURSAL',
            r'PART\s*-\s*II',
            r'BOUNDARIES',
            r'LIST\s+OF\s+DOCUMENTS',
            r'FLOW\s+OF\s+TITLE',
        ]

        for start_pattern in desc_start_patterns:
            for end_pattern in desc_end_patterns:
                pattern = start_pattern + r'(.*?)' + end_pattern
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    result["property_description"] = match.group(1).strip()
                    break
            if result["property_description"]:
                break

        return result
    def _build_prompt(self, text: str) -> str:

        return f"""
    Extract exactly these 7 fields from the legal property document.

    Return only JSON matching the required structure.

    Field rules:

    1. lsr_date:
    Look for date values near labels like: "LSR Date", "Date of Report", "Report Date", "Valuation Date", "Date:".
    Example format: 15/01/2024 or 15-01-2024

    2. company_name:
    Look for the lender/financial institution name near labels like: "Company Name", "Lender Name", "Bank Name", "Financial Institution", "Company", "Lender", "Bank".
    Example: ABC Housing Finance Ltd, Bajaj Finance Limited

    3. applicant_name:
    Look for the primary applicant/borrower name near labels like: "Applicant Name", "Borrower Name", "Applicant", "Proposed Borrower", "Borrower".

    4. co_applicant_name:
    Look for co-applicant/co-borrower name near labels like: "Co-Applicant Name", "Co-Applicant", "Co-Borrower", "Joint Applicant".

    5. property_owner:
    Look for the property owner/title holder name near labels like: "Property Owner", "Owner Name", "Title Holder", "Owner".

    6. application_number:
    Look for application/file/reference number near labels like: "Application Number", "Application No", "File No", "Reference No", "App No", "App. No.".
    Example format: APP/2024/001234, HL0000000356908

    7. property_description:
    Extract the complete property description text.
    Look for sections starting with "Property Description", "Description of Property", "Property Details", "PART - I: DESCRIPTION OF THE PROPERTY".
    Include all lines until the next major section (like "DOCUMENTS PRIOR TO DISBURSAL", "PART II", "BOUNDARIES", "LIST OF DOCUMENTS").
    Include address, survey/khewat/khatoni details, extent, measurements and boundaries.

    Rules:
    - Do not guess.
    - Preserve names and numbers exactly as they appear in the document.
    - If a field cannot be found, return null.
    - Do not combine different fields.
    - Return JSON only.

    DOCUMENT:
    {text}
    """.strip()

    def _parse_response(self, response: str) -> dict:
        """Convert LLM JSON response into a Python dictionary.

        Attempts multiple repair strategies for common LLM JSON issues:
        - Truncated/unterminated strings
        - Missing closing braces/brackets
        - Trailing commas
        - Markdown code fences
        """

        if not response or not response.strip():
            raise RuntimeError(
                "LLM returned an empty response."
            )

        # Strip markdown code fences if present
        # (e.g. ```json ... ``` or ``` ... ```)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Remove the opening fence (``` or ```json)
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            # Remove a closing fence if present
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        # Try direct parse first
        try:
            data = json.loads(cleaned)
            return self._extract_fields(data)
        except json.JSONDecodeError:
            pass

        # Attempt repair strategies
        repaired = self._attempt_json_repair(cleaned)
        if repaired is not None:
            return self._extract_fields(repaired)

        raise RuntimeError(
            "LLM returned invalid JSON that could not be repaired."
        )

    def _attempt_json_repair(self, text: str) -> dict | None:
        """Try multiple strategies to repair truncated/malformed JSON."""

        # Strategy 1: Fix unterminated strings by finding last complete value
        try:
            # Find the last complete key-value pair
            # Pattern: "key": "value" or "key": null or "key": number
            last_complete = self._find_last_complete_pair(text)
            if last_complete:
                # Close the object properly
                fixed = last_complete + "}"
                data = json.loads(fixed)
                print("[OK] Repaired truncated JSON (strategy 1: last complete pair)")
                return data
        except json.JSONDecodeError:
            pass

        # Strategy 2: Try closing unterminated strings
        try:
            fixed = self._close_unterminated_strings(text)
            data = json.loads(fixed)
            print("[OK] Repaired truncated JSON (strategy 2: closed strings)")
            return data
        except json.JSONDecodeError:
            pass

        # Strategy 3: Remove trailing commas and close braces
        try:
            fixed = text.rstrip()
            # Remove trailing commas before } or ]
            fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
            # Count open vs close braces (ensure non-negative)
            open_braces = max(0, fixed.count('{') - fixed.count('}'))
            open_brackets = max(0, fixed.count('[') - fixed.count(']'))
            fixed += ']' * open_brackets + '}' * open_braces
            data = json.loads(fixed)
            print("[OK] Repaired truncated JSON (strategy 3: trailing commas + close braces)")
            return data
        except json.JSONDecodeError:
            pass

        # Strategy 4: Extract individual field values with regex from malformed JSON
        try:
            return self._extract_from_malformed_json(text)
        except Exception:
            pass

        return None

    def _find_last_complete_pair(self, text: str) -> str | None:
        """Find text up to the last complete key-value pair in JSON."""
        # Match patterns like: "key": "value" or "key": null or "key": number
        pattern = r'"(\w+)":\s*("(?:[^"\\]|\\.)*"|null|-?\d+(?:\.\d+)?|true|false)'
        matches = list(re.finditer(pattern, text))
        if not matches:
            return None
        # Return everything up to and including the last complete match
        last_match = matches[-1]
        return text[:last_match.end()]

    def _close_unterminated_strings(self, text: str) -> str:
        """Attempt to close unterminated strings in JSON."""
        result = text.rstrip()

        # If the text ends with an unterminated string value
        # (odd number of unescaped quotes at the end)
        quote_count = 0
        last_backslash = False
        for ch in result:
            if ch == '\\' and not last_backslash:
                last_backslash = True
                continue
            if ch == '"' and not last_backslash:
                quote_count += 1
            last_backslash = False

        if quote_count % 2 != 0:
            # Unterminated string - close it and close the object
            result += '"'

        # Close any open structures
        open_braces = result.count('{') - result.count('}')
        open_brackets = result.count('[') - result.count(']')
        result += ']' * max(0, open_brackets)
        result += '}' * max(0, open_braces)

        return result

    def _extract_from_malformed_json(self, text: str) -> dict:
        """Extract field values directly from malformed JSON using regex."""
        result = {field: None for field in REQUIRED_FIELDS}

        # Try to extract each field using regex
        for field in REQUIRED_FIELDS:
            # Pattern: "field": "value" or "field": null
            pattern = rf'"{field}":\s*"((?:[^"\\]|\\.)*)"'
            match = re.search(pattern, text)
            if match:
                value = match.group(1)
                # Unescape JSON string escapes
                value = value.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                result[field] = value
            else:
                # Check for null
                null_pattern = rf'"{field}":\s*null'
                if re.search(null_pattern, text):
                    result[field] = None

        # Verify we got at least some fields
        non_null = sum(1 for v in result.values() if v is not None)
        if non_null > 0:
            print(f"[OK] Extracted {non_null} fields from malformed JSON via regex")
            return result

        raise ValueError("Could not extract any fields from malformed JSON")

    def _extract_fields(self, data: dict) -> dict:
        """Extract our predefined fields from parsed JSON data."""
        if not isinstance(data, dict):
            raise RuntimeError(
                "LLM response must be a JSON object."
            )

        result = {
            field: data.get(field)
            for field in REQUIRED_FIELDS
        }
        print(result)
        return result