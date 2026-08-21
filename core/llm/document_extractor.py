import json
import re
import time

from .freellm_client import FreeLLMClient


class DocumentExtractor:
    """
    Extracts documents required before and after loan disbursal.

    Uses FreeLLMClient instead of Ollama.

    Output for every document:

    {
        "document_name": str | None,
        "document_number": str | None,
        "document_date": str | None,
        "document_copy_type": str | None,
        "additional_details": str | None
    }
    """

    def __init__(self, llm_client: FreeLLMClient):
        self.llm = llm_client

    # ============================================================
    # PROMPT
    # ============================================================

    def _build_prompt(self, text: str) -> str:

        return f"""
Extract ONLY the documents listed under these two sections:

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
- document_copy_type
- additional_details


============================================================
DOCUMENT SEPARATION RULES
============================================================

1. Treat every listed document as an independent record.

2. Information belongs ONLY to the document where it is
   explicitly associated.

3. NEVER copy information from another document.

4. NEVER carry a date from the previous document to the next.

5. NEVER carry a number from the previous document to the next.

6. NEVER carry "issued by", "in the name of", "executed by",
   "in favour of", or similar information from another document.


============================================================
DOCUMENT NAME
============================================================

7. document_name must contain ONLY the actual document name.

8. NEVER include the document date in document_name.

9. NEVER include the document number in document_name.

10. Remove phrases such as:

    dated 25-09-1998
    dated 05-02-2001
    No.2867/1998

Example:

Source:
Partition Deed No.2867/1998 dated 25-09-1998

Correct:

"document_name": "Partition Deed"


============================================================
DOCUMENT NUMBER
============================================================

11. document_number must contain ONLY an actual document
    or reference number.

12. Valid examples:

    2867/1998
    123/2020
    4567

13. The following are NOT document numbers:

    issued by Greater Chennai Corporation
    issued by Tahsildar, Egmore Taluk
    in the name of Vasantha Kumar
    executed by Mrs.Indumathi
    executed by Mrs.Bhuvaneshwari
    in favour of a company
    Original
    Xerox
    Online

14. If no actual document number exists:

    "document_number": null


============================================================
DOCUMENT DATE
============================================================

15. document_date must contain ONLY an actual date.

16. Preserve the date exactly as written in the source.

17. If the document does not explicitly contain a date:

    "document_date": null

18. NEVER infer a date.

19. NEVER copy a date from another document.

20. A date belongs ONLY to the document to which it is
    explicitly associated.


============================================================
DOCUMENT COPY TYPE
============================================================

21. document_copy_type represents the copy type explicitly
    mentioned for the document.

Possible values include:

    Original
    Xerox
    Photocopy
    Certified Copy
    Certified
    Online Copy
    Online

22. Extract the copy type exactly as stated.

23. Do NOT guess the copy type.

24. Do NOT copy the copy type from another document.

25. If the copy type is not explicitly available:

    "document_copy_type": null

26. Copy type MUST NEVER be placed inside document_number.


============================================================
ADDITIONAL DETAILS
============================================================

27. additional_details contains useful descriptive/reference
    information that does NOT belong in:

    - document_name
    - document_number
    - document_date
    - document_copy_type

28. Examples:

    issued by Greater Chennai Corporation

    issued by Tahsildar, Egmore Taluk

    in the name of Vasantha Kumar

    executed by Mrs.Indumathi

    executed by Mrs.Bhuvaneshwari and Mrs.Malini

    in favour of Vastu Housing Finance Corporation Limited

29. Preserve additional details whenever they are explicitly
    associated with the current document.

30. NEVER put descriptive information inside document_number.

31. NEVER put descriptive information inside document_date.

32. NEVER put copy type inside additional_details.

33. If there is no useful additional information:

    "additional_details": null


============================================================
MISSING VALUES
============================================================

34. Never guess.

35. Never infer.

36. Use null when information is not explicitly available.

37. Missing document number:

    "document_number": null

38. Missing document date:

    "document_date": null

39. Missing document copy type:

    "document_copy_type": null

40. Missing additional information:

    "additional_details": null


============================================================
IMPORTANT EXAMPLES
============================================================

Example 1:

Source:

Partition Deed No.2867/1998 dated 25-09-1998
Original

Output:

{{
    "document_name": "Partition Deed",
    "document_number": "2867/1998",
    "document_date": "25-09-1998",
    "document_copy_type": "Original",
    "additional_details": null
}}


Example 2:

Source:

Town Survey Field Register Extract dated 05-02-2001
in the name of Mr.Vasantha Kumar
Original

Output:

{{
    "document_name": "Town Survey Field Register Extract",
    "document_number": null,
    "document_date": "05-02-2001",
    "document_copy_type": "Original",
    "additional_details": "in the name of Mr.Vasantha Kumar"
}}


Example 3:

Source:

Death Certificate of Vasantha Kumar
issued by Greater Chennai Corporation
Online

Output:

{{
    "document_name": "Death Certificate of Vasantha Kumar",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Online",
    "additional_details": "issued by Greater Chennai Corporation"
}}


Example 4:

Source:

Legal Heir-Ship Certificate of Vasantha Kumar
issued by Tahsildar, Egmore Taluk
Online

Output:

{{
    "document_name": "Legal Heir-Ship Certificate of Vasantha Kumar",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Online",
    "additional_details": "issued by Tahsildar, Egmore Taluk"
}}


Example 5:

Source:

Property Tax Receipt
in the name of Vasantha Kumar
Xerox

Output:

{{
    "document_name": "Property Tax Receipt",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Xerox",
    "additional_details": "in the name of Vasantha Kumar"
}}


Example 6:

Source:

Proposed MODTD in favour of Vastu Housing Finance Corporation Limited
Original

Output:

{{
    "document_name": "Proposed MODTD",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Original",
    "additional_details": "in favour of Vastu Housing Finance Corporation Limited"
}}


============================================================
FINAL JSON STRUCTURE
============================================================

Return ONLY this JSON:

{{
    "documents_prior_to_disbursal": [
        {{
            "document_name": null,
            "document_number": null,
            "document_date": null,
            "document_copy_type": null,
            "additional_details": null
        }}
    ],

    "documents_post_disbursal": [
        {{
            "document_name": null,
            "document_number": null,
            "document_date": null,
            "document_copy_type": null,
            "additional_details": null
        }}
    ]
}}

Do NOT return markdown.
Do NOT return explanations.
Return valid JSON only.


============================================================
DOCUMENT TEXT
============================================================

{text}

""".strip()

    # ============================================================
    # JSON PARSING
    # ============================================================

    def _parse_response(self, response: str) -> dict:

        if not response or not response.strip():
            raise RuntimeError(
                "FreeLLM returned an empty response."
            )

        cleaned_response = response.strip()

        # Remove accidental markdown fences.
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]

        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        cleaned_response = cleaned_response.strip()

        try:
            data = json.loads(cleaned_response)

        except json.JSONDecodeError as exc:

            print(
                "\n========== INVALID FREELLM RESPONSE =========="
            )
            print(response)
            print("==============================================\n")

            raise RuntimeError(
                f"FreeLLM returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "FreeLLM response must be a JSON object."
            )

        return data

    # ============================================================
    # DOCUMENT NAME CLEANING
    # ============================================================

    def _clean_document_name(self, value):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        # Remove "dated <date>"
        value = re.sub(
            r"\s+dated\s*:?\s*"
            r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",
            "",
            value,
            flags=re.IGNORECASE,
        )

        # Remove "No.123/2020"
        value = re.sub(
            r"\s+No\.?\s*[A-Za-z0-9/-]+",
            "",
            value,
            flags=re.IGNORECASE,
        )

        # Remove trailing standalone date.
        value = re.sub(
            r"\s+"
            r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
            r"$",
            "",
            value,
        )

        return value.strip(" -,:;")

    # ============================================================
    # DOCUMENT NUMBER VALIDATION
    # ============================================================

    def _is_valid_document_number(self, value):

        if value is None:
            return False

        value = str(value).strip()

        if not value:
            return False

        lower = value.lower()

        invalid_phrases = [
            "issued by",
            "in the name of",
            "executed by",
            "in favour of",
            "in favor of",
            "original",
            "xerox",
            "photocopy",
            "online",
            "certified",
            "not specified",
            "not available",
        ]

        for phrase in invalid_phrases:

            if phrase in lower:
                return False

        # Actual document/reference numbers should
        # normally contain at least one digit.
        if not re.search(r"\d", value):
            return False

        return True

    # ============================================================
    # DOCUMENT DATE CLEANING
    # ============================================================

    def _clean_document_date(self, value):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        match = re.search(
            r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",
            value,
        )

        if not match:
            return None

        return match.group(0)

    # ============================================================
    # COPY TYPE CLEANING
    # ============================================================

    def _clean_copy_type(self, value):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        copy_types = {
            "original": "Original",
            "xerox": "Xerox",
            "photocopy": "Photocopy",
            "certified copy": "Certified Copy",
            "certified": "Certified",
            "online copy": "Online Copy",
            "online": "Online",
        }

        lower_value = value.lower()

        for key, clean_value in copy_types.items():

            if lower_value == key:
                return clean_value

        return None

    # ============================================================
    # ADDITIONAL DETAILS CLEANING
    # ============================================================

    def _clean_additional_details(self, value):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        invalid_values = {
            "null",
            "none",
            "n/a",
            "na",
            "not specified",
            "not available",
        }

        if value.lower() in invalid_values:
            return None

        return value

    # ============================================================
    # NORMALIZE ONE DOCUMENT
    # ============================================================

    def _normalize_document(self, document):

        if not isinstance(document, dict):
            return None

        document_name = self._clean_document_name(
            document.get("document_name")
        )

        document_number = None

        original_number = document.get(
            "document_number"
        )

        if self._is_valid_document_number(
            original_number
        ):
            document_number = str(
                original_number
            ).strip()

        document_date = self._clean_document_date(
            document.get("document_date")
        )

        document_copy_type = self._clean_copy_type(
            document.get("document_copy_type")
        )

        additional_details = (
            self._clean_additional_details(
                document.get("additional_details")
            )
        )

        # --------------------------------------------------------
        # IMPORTANT:
        # If LLM incorrectly placed descriptive information
        # inside document_number, move it to additional_details.
        # --------------------------------------------------------

        if original_number and document_number is None:

            invalid_number = str(
                original_number
            ).strip()

            if additional_details:

                if invalid_number.lower() not in (
                    additional_details.lower()
                ):
                    additional_details = (
                        f"{additional_details}; "
                        f"{invalid_number}"
                    )

            else:

                additional_details = invalid_number

        return {
            "document_name": document_name,
            "document_number": document_number,
            "document_date": document_date,
            "document_copy_type": document_copy_type,
            "additional_details": additional_details,
        }

    # ============================================================
    # NORMALIZE DOCUMENT LIST
    # ============================================================

    def _normalize_documents(self, documents):

        if not isinstance(documents, list):
            return []

        normalized = []

        for document in documents:

            cleaned = self._normalize_document(
                document
            )

            if cleaned is not None:
                normalized.append(cleaned)

        return normalized

    # ============================================================
    # MAIN EXTRACTION
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

        # ========================================================
        # PROMPT CONSTRUCTION
        # ========================================================

        start = time.perf_counter()

        prompt = self._build_prompt(text)

        prompt_time = (
            time.perf_counter() - start
        )

        print(
            f"⏱️ Prompt construction: "
            f"{prompt_time:.2f} seconds"
        )

        print(
            f"📝 Prompt characters: "
            f"{len(prompt)}"
        )

        # ========================================================
        # FREELLM
        # ========================================================

        start = time.perf_counter()

        response = self.llm.generate(
            prompt
        )

        llm_time = (
            time.perf_counter() - start
        )

        print(
            f"⏱️ FreeLLM response: "
            f"{llm_time:.2f} seconds"
        )

        print(
            "\n========== RAW FREELLM DOCUMENT RESPONSE =========="
        )

        print(response)

        print(
            "===================================================="
        )

        # ========================================================
        # JSON PARSING
        # ========================================================

        start = time.perf_counter()

        data = self._parse_response(
            response
        )

        parsing_time = (
            time.perf_counter() - start
        )

        print(
            f"⏱️ JSON parsing: "
            f"{parsing_time:.2f} seconds"
        )

        # ========================================================
        # NORMALIZE DOCUMENTS
        # ========================================================

        prior_documents = (
            self._normalize_documents(
                data.get(
                    "documents_prior_to_disbursal",
                    [],
                )
            )
        )

        post_documents = (
            self._normalize_documents(
                data.get(
                    "documents_post_disbursal",
                    [],
                )
            )
        )

        result = {
            "documents_prior_to_disbursal":
                prior_documents,

            "documents_post_disbursal":
                post_documents,
        }

        # ========================================================
        # FINAL DEBUG OUTPUT
        # ========================================================

        print("\n")
        print(
            "========== CLEAN DOCUMENT RESULT =========="
        )

        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False,
            )
        )

        print(
            "============================================"
        )

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