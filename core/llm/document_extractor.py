import json
import re
import time

from core.llm.freellm_client import FreeLLMClient


class DocumentExtractor:
    """
    Extract documents required before and after loan disbursal.

    Uses FreeLLMClient for LLM-based extraction.

    Output structure:

    {
        "documents_prior_to_disbursal": [
            {
                "document_name": str | None,
                "document_number": str | None,
                "document_date": str | None,
                "document_copy_type": str | None,
                "additional_details": str | None
            }
        ],
        "documents_post_disbursal": [
            ...
        ]
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

For every document return EXACTLY these fields:

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

8. Do NOT put the document date inside document_name.

9. Do NOT put the document number inside document_name.

Example:

Source:
Partition Deed No.2867/1998 dated 25-09-1998

Correct:

"document_name": "Partition Deed"


============================================================
DOCUMENT NUMBER
============================================================

10. document_number must contain ONLY an actual document,
    registration, certificate, patta or reference number.

Valid examples:

2867/1998
123/2020
4567
11204

11. These are NOT document numbers:

- issued by Greater Chennai Corporation
- issued by Tahsildar
- in the name of Vasantha Kumar
- executed by Mrs.Indumathi
- in favour of a company
- Original
- Xerox
- Online

12. If an actual document number is not present,
    return null.

13. Do NOT invent a number.


============================================================
DOCUMENT DATE
============================================================

14. Extract the actual date associated with the document.

Example:

Partition Deed dated 25-09-1998

Correct:

"document_date": "25-09-1998"

15. If the date is not present, return null.

16. NEVER copy a date from another document.


============================================================
DOCUMENT TYPE
============================================================

17. document_copy_type tells whether the document is:

- Original
- Xerox
- Online
- Photocopy
- Certified Copy
- Certified

18. If the source explicitly says "Original",
    return:

"document_copy_type": "Original"

19. If the source explicitly says "Xerox",
    return:

"document_copy_type": "Xerox"

20. If the source explicitly says "Online",
    return:

"document_copy_type": "Online"

21. If the source explicitly says "Photocopy",
    return:

"document_copy_type": "Photocopy"

22. If the source explicitly says "Certified Copy",
    return:

"document_copy_type": "Certified Copy"

23. Do NOT put Original/Xerox/Online inside document_number.

24. Do NOT put Original/Xerox/Online inside additional_details.

25. If copy type is not explicitly available, return null.


============================================================
ADDITIONAL DETAILS
============================================================

26. additional_details is for useful descriptive information
    that does NOT belong in document_name, document_number,
    document_date, or document_copy_type.

Examples:

- issued by Greater Chennai Corporation
- issued by Tahsildar, Egmore Taluk
- in the name of Vasantha Kumar
- executed by a named person
- in favour of a named company

27. If document_number is null AND document_date is null,
    preserve useful reference information in additional_details.

28. If document_number OR document_date exists,
    additional_details should normally be null.

29. Do NOT move document type into additional_details.

30. Do NOT invent information.


============================================================
EXAMPLE 1
============================================================

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


============================================================
EXAMPLE 2
============================================================

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
    "additional_details": null
}}


============================================================
EXAMPLE 3
============================================================

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


============================================================
EXAMPLE 4
============================================================

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


============================================================
EXAMPLE 5
============================================================

Source:

Property Tax Receipt in the name of Vasantha Kumar
Xerox

Output:

{{
    "document_name": "Property Tax Receipt",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Xerox",
    "additional_details": "in the name of Vasantha Kumar"
}}


============================================================
EXAMPLE 6
============================================================

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

Return ONLY valid JSON.

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
Return JSON only.


============================================================
DOCUMENT TEXT
============================================================

{text}

""".strip()

    # ============================================================
    # JSON EXTRACTION
    # ============================================================

    def _extract_json_block(self, response: str) -> str:
        """
        Extract JSON object from an LLM response.

        Handles responses such as:

        ```json
        {...}
        ```

        or plain JSON.
        """

        if not response:
            raise ValueError(
                "FreeLLM returned an empty response."
            )

        response = response.strip()

        # Remove markdown code fences
        response = re.sub(
            r"^```(?:json)?\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"\s*```$",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = response.strip()

        # Find first JSON object
        start = response.find("{")

        if start == -1:
            raise ValueError(
                "No JSON object found in FreeLLM response."
            )

        # Find matching closing brace
        depth = 0
        in_string = False
        escaped = False

        for index in range(start, len(response)):

            char = response[index]

            if escaped:
                escaped = False
                continue

            if char == "\\" and in_string:
                escaped = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1

            elif char == "}":
                depth -= 1

                if depth == 0:
                    return response[
                        start:index + 1
                    ]

        raise ValueError(
            "Incomplete JSON object returned by FreeLLM."
        )

    # ============================================================
    # JSON PARSING
    # ============================================================

    def _parse_response(self, response: str) -> dict:

        json_text = self._extract_json_block(
            response
        )

        try:

            data = json.loads(
                json_text
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                f"Invalid JSON returned by FreeLLM: {exc}"
            ) from exc

        if not isinstance(data, dict):

            raise ValueError(
                "FreeLLM response must be a JSON object."
            )

        return data

    # ============================================================
    # DOCUMENT NAME CLEANING
    # ============================================================

    def _clean_document_name(
        self,
        value,
    ):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        # Remove "dated 25-09-1998"
        value = re.sub(
            r"\s+dated\s*:?\s*"
            r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",
            "",
            value,
            flags=re.IGNORECASE,
        )

        # Remove "No.2867/1998"
        value = re.sub(
            r"\s+No\.?\s*[A-Za-z0-9/-]+",
            "",
            value,
            flags=re.IGNORECASE,
        )

        # Remove standalone trailing date
        value = re.sub(
            r"\s+"
            r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
            r"$",
            "",
            value,
        )

        # Remove accidental trailing copy type
        value = re.sub(
            r"\s+(Original|Xerox|Online|Photocopy)$",
            "",
            value,
            flags=re.IGNORECASE,
        )

        return value.strip(
            " -,:;"
        )

    # ============================================================
    # DOCUMENT NUMBER VALIDATION
    # ============================================================

    def _clean_document_number(
        self,
        value,
    ):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

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
            "n/a",
        ]

        for phrase in invalid_phrases:

            if phrase in lower:
                return None

        # Must contain at least one digit.
        if not re.search(
            r"\d",
            value,
        ):
            return None

        return value

    # ============================================================
    # DOCUMENT DATE CLEANING
    # ============================================================

    def _clean_document_date(
        self,
        value,
    ):

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
    # DOCUMENT TYPE CLEANING
    # ============================================================

    def _clean_copy_type(
        self,
        value,
    ):

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        normalized = value.lower()

        copy_types = {
            "original": "Original",
            "xerox": "Xerox",
            "photocopy": "Photocopy",
            "certified copy": "Certified Copy",
            "certified": "Certified",
            "online copy": "Online",
            "online": "Online",
        }

        return copy_types.get(
            normalized
        )

    # ============================================================
    # ADDITIONAL DETAILS CLEANING
    # ============================================================

    def _clean_additional_details(
        self,
        value,
    ):

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

    def _normalize_document(
        self,
        document,
    ):

        if not isinstance(
            document,
            dict,
        ):
            return None

        document_name = (
            self._clean_document_name(
                document.get(
                    "document_name"
                )
            )
        )

        document_number = (
            self._clean_document_number(
                document.get(
                    "document_number"
                )
            )
        )

        document_date = (
            self._clean_document_date(
                document.get(
                    "document_date"
                )
            )
        )

        document_copy_type = (
            self._clean_copy_type(
                document.get(
                    "document_copy_type"
                )
            )
        )

        additional_details = (
            self._clean_additional_details(
                document.get(
                    "additional_details"
                )
            )
        )

        # --------------------------------------------------------
        # If LLM incorrectly placed descriptive information
        # inside document_number, move it to additional_details.
        # --------------------------------------------------------

        original_number = document.get(
            "document_number"
        )

        if (
            original_number
            and document_number is None
        ):

            invalid_number = str(
                original_number
            ).strip()

            if additional_details:

                if (
                    invalid_number.lower()
                    not in
                    additional_details.lower()
                ):

                    additional_details = (
                        f"{additional_details}; "
                        f"{invalid_number}"
                    )

            else:

                additional_details = (
                    invalid_number
                )

        # --------------------------------------------------------
        # If number or date exists, descriptive details should
        # not override the actual number/date.
        # --------------------------------------------------------

        if (
            document_number
            or document_date
        ):
            additional_details = None

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

    def _normalize_documents(
        self,
        documents,
    ):

        if not isinstance(
            documents,
            list,
        ):
            return []

        normalized = []

        for document in documents:

            clean_document = (
                self._normalize_document(
                    document
                )
            )

            if clean_document is not None:

                normalized.append(
                    clean_document
                )

        return normalized

    # ============================================================
    # MAIN EXTRACTION
    # ============================================================

    def extract_documents(
        self,
        text: str,
    ) -> dict:

        if not text or not text.strip():

            raise ValueError(
                "OCR text cannot be empty."
            )

        print("\n")
        print("=" * 55)
        print(
            "DOCUMENT LIST EXTRACTION STARTED"
        )
        print("=" * 55)

        print(
            f"📝 Input characters: "
            f"{len(text)}"
        )

        print(
            f"📝 Input words: "
            f"{len(text.split())}"
        )

        # ========================================================
        # PROMPT
        # ========================================================

        prompt_start = time.perf_counter()

        prompt = self._build_prompt(
            text
        )

        prompt_time = (
            time.perf_counter()
            - prompt_start
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

        llm_start = time.perf_counter()

        response = self.llm.generate(
            prompt
        )

        llm_time = (
            time.perf_counter()
            - llm_start
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

        parse_start = time.perf_counter()

        try:

            data = self._parse_response(
                response
            )

        except ValueError as exc:

            print(
                f"❌ Document JSON parsing failed: {exc}"
            )

            raise RuntimeError(
                f"Document extraction returned invalid JSON: {exc}"
            ) from exc

        parse_time = (
            time.perf_counter()
            - parse_start
        )

        print(
            f"⏱️ JSON parsing: "
            f"{parse_time:.2f} seconds"
        )

        # ========================================================
        # NORMALIZE PRIOR DOCUMENTS
        # ========================================================

        prior_documents = (
            self._normalize_documents(
                data.get(
                    "documents_prior_to_disbursal",
                    [],
                )
            )
        )

        # ========================================================
        # NORMALIZE POST DOCUMENTS
        # ========================================================

        post_documents = (
            self._normalize_documents(
                data.get(
                    "documents_post_disbursal",
                    [],
                )
            )
        )

        # ========================================================
        # FINAL RESULT
        # ========================================================

        result = {
            "documents_prior_to_disbursal":
                prior_documents,

            "documents_post_disbursal":
                post_documents,
        }

        # ========================================================
        # DEBUG
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