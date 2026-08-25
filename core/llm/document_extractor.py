import json
import time
import re


class DocumentExtractor:
    """
    Extracts documents required before and after loan disbursal.

    Output structure for every document:

    {
        "document_name": str | None,
        "document_number": str | None,
        "document_date": str | None,
        "mode_of_document": str | None,
        "additional_details": str | None
    }

    additional_details is used ONLY when BOTH
    document_number and document_date are unavailable.
    """

    def __init__(self, ollama_client):
        self.ollama = ollama_client

    # ============================================================
    # JSON REPAIR HELPERS (for truncated LLM responses)
    # ============================================================

    def _attempt_json_repair(self, text: str) -> dict | None:
        """Try multiple strategies to repair truncated/malformed JSON."""

        # Strategy 1: Fix unterminated strings by finding last complete value
        try:
            # Find the last complete key-value pair
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
            # Count open vs close braces
            open_braces = fixed.count('{') - fixed.count('}')
            open_brackets = fixed.count('[') - fixed.count(']')
            fixed += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
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
        result = {
            "documents_prior_to_disbursal": [],
            "documents_post_disbursal": []
        }

        # Try to extract documents_prior_to_disbursal array
        prior_match = re.search(r'"documents_prior_to_disbursal"\s*:\s*(\[.*?\])', text, re.DOTALL)
        if prior_match:
            try:
                prior_data = json.loads(prior_match.group(1))
                if isinstance(prior_data, list):
                    result["documents_prior_to_disbursal"] = prior_data
            except json.JSONDecodeError:
                pass

        # Try to extract documents_post_disbursal array
        post_match = re.search(r'"documents_post_disbursal"\s*:\s*(\[.*?\])', text, re.DOTALL)
        if post_match:
            try:
                post_data = json.loads(post_match.group(1))
                if isinstance(post_data, list):
                    result["documents_post_disbursal"] = post_data
            except json.JSONDecodeError:
                pass

        # Verify we got at least some data
        total_docs = len(result["documents_prior_to_disbursal"]) + len(result["documents_post_disbursal"])
        if total_docs > 0:
            print(f"✅ Extracted {total_docs} documents from malformed JSON via regex")
            return result

        raise ValueError("Could not extract any documents from malformed JSON")

    # ============================================================
    # PROMPT
    # ============================================================

    def _build_prompt(self, text: str) -> str:

        return f"""
Extract ONLY the documents listed under:

1. Steps / Documents Prior to disbursal
2. Documents required post disbursal

Ignore:
- List of all Documents that were perused and verified
- Documents mentioned elsewhere in the legal report
- Documents from tracing of title
- Documents from other sections

For every document return exactly these fields:

- document_name
- document_number
- document_date
- mode_of_document
- additional_details


IMPORTANT RULES:

1. document_name must contain ONLY the actual document name.

2. NEVER include the document date inside document_name.

WRONG:
"Partition Deed dated 25-09-1998"

CORRECT:
"Partition Deed"


3. document_number must contain ONLY an actual
document/reference number.

Example:

"2867/1998"


4. document_date must contain ONLY an actual date.

Example:

"25-09-1998"


5. NEVER put descriptive information inside
document_number or document_date.

The following are NOT document numbers or dates:

- issued by Greater Chennai Corporation
- issued by Tahsildar
- in the name of Vasantha Kumar
- executed by Mrs.Indumathi
- in favour of a company


6. If document_number is not present, return null.

7. If document_date is not present, return null.


8. additional_details MUST be used ONLY when BOTH:

document_number is null
AND
document_date is null


9. When BOTH document_number and document_date are missing,
use additional_details to preserve useful reference information.

Examples of useful additional details:

- issued by Greater Chennai Corporation
- issued by Tahsildar, Egmore Taluk
- in the name of Vasantha Kumar
- executed by a named person
- in favour of a named company


10. If EITHER document_number OR document_date exists,
additional_details MUST be null.


11. Never invent or guess a document number or date.

12. Keep information belonging to the same document together.

13. Preserve the values appearing in the source document.

14. If no documents are present under a section,
return an empty list.

15. Return ONLY valid JSON.
Do not return explanations or markdown.


16. mode_of_document must contain the document condition
as one of: "Original", "Copy", "Xerox", "Online", or "Certified Copy".

17. If the source text mentions "(Original)" or "original" near the
document, return "Original".

18. If the source text mentions "(Copy)", "xerox", or "photocopy",
return "Copy" or "Xerox".

19. If the source text mentions "Online Patta" or "Online EC",
return "Online".

20. If the source text mentions "Certified Copy", return "Certified Copy".

21. If no mode information is available, return null for mode_of_document.


EXAMPLE 1

Input:

Partition Deed No.2867/1998 dated 25-09-1998

Output:

{{
    "document_name": "Partition Deed",
    "document_number": "2867/1998",
    "document_date": "25-09-1998",
    "mode_of_document": null,
    "additional_details": null
}}


EXAMPLE 2

Input:

Town Survey Field Register Extract dated 05-02-2001
in the name of Mr.Vasantha Kumar

Output:

{{
    "document_name": "Town Survey Field Register Extract",
    "document_number": null,
    "document_date": "05-02-2001",
    "mode_of_document": null,
    "additional_details": null
}}


EXAMPLE 3

Input:

Death Certificate of Vasantha Kumar
issued by Greater Chennai Corporation

Output:

{{
    "document_name": "Death Certificate of Vasantha Kumar",
    "document_number": null,
    "document_date": null,
    "mode_of_document": null,
    "additional_details": "issued by Greater Chennai Corporation"
}}


EXAMPLE 4

Input:

Online Patta No.11204 in the name of Mrs.Malleeshwari

Output:

{{
    "document_name": "Online Patta",
    "document_number": "11204",
    "document_date": null,
    "mode_of_document": "Online",
    "additional_details": "in the name of Mrs.Malleeshwari"
}}


EXAMPLE 5

Input:

Sale deed dated 13.03.2012 Doc. No. 1594/2012 in favour of Mr.Gopi (Original)

Output:

{{
    "document_name": "Sale Deed",
    "document_number": "1594/2012",
    "document_date": "13.03.2012",
    "mode_of_document": "Original",
    "additional_details": null
}}


Required JSON structure:

{{
    "documents_prior_to_disbursal": [
        {{
            "document_name": "...",
            "document_number": null,
            "document_date": null,
            "mode_of_document": null,
            "additional_details": null
        }}
    ],

    "documents_post_disbursal": [
        {{
            "document_name": "...",
            "document_number": null,
            "document_date": null,
            "mode_of_document": null,
            "additional_details": null
        }}
    ]
}}


DOCUMENT TEXT:

{text}

""".strip()

    # ============================================================
    # JSON PARSING
    # ============================================================

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
            return data
        except json.JSONDecodeError:
            pass

        # Attempt repair strategies
        repaired = self._attempt_json_repair(cleaned)
        if repaired is not None:
            return repaired

        raise RuntimeError(
            "LLM returned invalid JSON that could not be repaired."
        )

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def _normalize_documents(self, documents) -> list:

        if not isinstance(documents, list):
            return []

        normalized = []

        for document in documents:

            if not isinstance(document, dict):
                continue

            document_name = document.get(
                "document_name"
            )

            document_number = document.get(
                "document_number"
            )

            document_date = document.get(
                "document_date"
            )

            additional_details = document.get(
                "additional_details"
            )

            mode_of_document = document.get(
                "mode_of_document"
            )

            # ----------------------------------------------------
            # Enforce our business rule in Python too.
            #
            # If either number OR date exists,
            # additional_details must be null.
            # ----------------------------------------------------

            if document_number or document_date:
                additional_details = None

            normalized.append(
                {
                    "document_name":
                        document_name,

                    "document_number":
                        document_number,

                    "document_date":
                        document_date,

                    "mode_of_document":
                        mode_of_document,

                    "additional_details":
                        additional_details,
                }
            )

        return normalized

    # ============================================================
    # PUBLIC EXTRACTION METHOD
    # ============================================================

    def extract_documents(self, text: str) -> dict:

        if not text or not text.strip():
            raise ValueError(
                "OCR text cannot be empty."
            )

        print("\n")
        print("=" * 55)
        print("DOCUMENT LIST EXTRACTION STARTED")
        print("=" * 55)

        print(
            f"📝 Input characters: {len(text)}"
        )

        print(
            f"📝 Input words: {len(text.split())}"
        )

        # --------------------------------------------------------
        # Prompt construction
        # --------------------------------------------------------

        start = time.perf_counter()

        prompt = self._build_prompt(text)

        prompt_time = (
            time.perf_counter()
            - start
        )

        print(
            f"⏱️ Prompt construction: "
            f"{prompt_time:.2f} seconds"
        )

        print(
            f"📝 Prompt characters: "
            f"{len(prompt)}"
        )

        # --------------------------------------------------------
        # Ollama (with retry logic for empty responses and LLM failures)
        # --------------------------------------------------------

        start = time.perf_counter()

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
                    print("⚠️ LLM failed after retries, returning empty document lists...")
                    return {
                        "documents_prior_to_disbursal": [],
                        "documents_post_disbursal": []
                    }
            # Exponential backoff: 2s, 4s, 8s...
            wait_time = min(2 ** (attempt + 1), 30)
            time.sleep(wait_time)

        if not response or not response.strip():
            print("⚠️ LLM failed after retries, returning empty document lists...")
            return {
                "documents_prior_to_disbursal": [],
                "documents_post_disbursal": []
            }

        llm_time = (
            time.perf_counter()
            - start
        )

        print(
            f"⏱️ Ollama response: "
            f"{llm_time:.2f} seconds"
        )

        print(
            "\n========== RAW DOCUMENT RESPONSE =========="
        )

        print(response)

        print(
            "============================================"
        )

        # --------------------------------------------------------
        # JSON parsing (with fallback)
        # --------------------------------------------------------

        start = time.perf_counter()

        data = None

        try:
            data = self._parse_response(response)

            parsing_time = time.perf_counter() - start

            print(
                f"⏱️ JSON parsing: "
                f"{parsing_time:.2f} seconds"
            )

        except (RuntimeError, json.JSONDecodeError) as exc:
            print(f"⚠️ JSON parsing failed: {exc}")
            print("   No fallback available for document extraction - returning empty lists")
            data = {
                "documents_prior_to_disbursal": [],
                "documents_post_disbursal": []
            }

        # --------------------------------------------------------
        # Normalize prior documents
        # --------------------------------------------------------

        prior_documents = (
            self._normalize_documents(
                data.get(
                    "documents_prior_to_disbursal",
                    []
                )
            )
        )

        # --------------------------------------------------------
        # Normalize post documents
        # --------------------------------------------------------

        post_documents = (
            self._normalize_documents(
                data.get(
                    "documents_post_disbursal",
                    []
                )
            )
        )

        result = {
            "documents_prior_to_disbursal":
                prior_documents,

            "documents_post_disbursal":
                post_documents,
        }

        print(
            f"📋 Prior-disbursal documents: "
            f"{len(prior_documents)}"
        )

        print(
            f"📋 Post-disbursal documents: "
            f"{len(post_documents)}"
        )

        print("=" * 55)

        return result