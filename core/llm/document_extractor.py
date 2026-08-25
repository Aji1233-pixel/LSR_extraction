import json
import re
import time


class DocumentExtractor:
    """Extracts documents required before and after loan disbursal."""

    # Compiled Regex Patterns
    RE_DATE_DATED = re.compile(
        r"\s+dated\s*:?\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", re.IGNORECASE
    )
    RE_DOC_NUMBER = re.compile(r"\s+No\.?\s*[A-Za-z0-9/-]+", re.IGNORECASE)
    RE_TRAILING_DATE = re.compile(r"\s+\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$")
    RE_EXTRACT_DATE = re.compile(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}")
    RE_HAS_DIGIT = re.compile(r"\d")

    {
        "document_name": str | None,
        "document_number": str | None,
        "document_date": str | None,
        "additional_details": str | None
    }

    additional_details is used ONLY when BOTH
    document_number and document_date are unavailable.
    """

    def __init__(self, ollama_client):
        self.ollama = ollama_client

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
- additional_details


============================================================
DOCUMENT SEPARATION RULES
============================================================

1. Treat every listed document as an independent record.

2. Information belongs ONLY to the document it is explicitly
   associated with.

3. NEVER copy information from one document to another.

4. NEVER carry a date from the previous document to the next document.

5. NEVER carry a number from the previous document to the next document.

6. NEVER carry an "issued by", "in the name of", "executed by",
   or similar description from one document to another.


============================================================
DOCUMENT NAME
============================================================

7. document_name must contain ONLY the actual document name.

8. Do NOT include the document date in document_name.

9. Do NOT include the document number in document_name.

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

11. document_number must contain ONLY an actual document number
    or reference number.

12. Examples of valid document numbers:

    2867/1998
    123/2020
    4567
    Doc.No.1234

13. The following are NOT document numbers:

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


EXAMPLE 1

Input:

Partition Deed No.2867/1998 dated 25-09-1998
Original

Output:

{{
    "document_name": "Partition Deed",
    "document_number": "2867/1998",
    "document_date": "25-09-1998",
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
    "additional_details": null
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
    "additional_details": "issued by Greater Chennai Corporation"
}}


EXAMPLE 4

Input:

Property Tax Receipt in the name of Vasantha Kumar

Output:

{{
    "document_name": "Online Patta",
    "document_number": "11204",
    "document_date": null,
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

Return ONLY this JSON structure:

{{
    "documents_prior_to_disbursal": [
        {{
            "document_name": "...",
            "document_number": null,
            "document_date": null,
            "additional_details": null
        }}
    ],

    "documents_post_disbursal": [
        {{
            "document_name": "...",
            "document_number": null,
            "document_date": null,
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

    def _parse_response(self, response: str) -> dict:

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON returned by LLM: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "LLM response must be a JSON object."
            )

        return data

    def _clean_document_name(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        if not val:
            return None

        # Clean "dated <date>" and "dated: <date>" via single precompiled pattern
        val = self.RE_DATE_DATED.sub("", val)
        val = self.RE_DOC_NUMBER.sub("", val)
        val = self.RE_TRAILING_DATE.sub("", val)

        val = val.strip(" -,:;")
        return val if val else None

    def _is_valid_document_number(self, value) -> bool:
        if not value:
            return False

        val = str(value).strip()
        if not val:
            return False

        lower = val.lower()
        if any(phrase in lower for phrase in self.INVALID_PHRASES):
            return False

        return bool(self.RE_HAS_DIGIT.search(val))

    def _clean_document_date(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        if not val:
            return None

        match = self.RE_EXTRACT_DATE.search(val)
        return match.group(0) if match else None

    def _clean_copy_type(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        return self.COPY_TYPES.get(val.lower())

    def _clean_additional_details(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        if not val or val.lower() in self.INVALID_DETAILS:
            return None

        return val

    def _normalize_document(self, document: dict) -> dict | None:
        if not isinstance(document, dict):
            return None

        cleaned_name = self._clean_document_name(document.get("document_name"))
        cleaned_date = self._clean_document_date(document.get("document_date"))
        cleaned_copy = self._clean_copy_type(document.get("document_copy_type"))
        cleaned_details = self._clean_additional_details(
            document.get("additional_details")
        )

        doc_num = None
        original_number = document.get("document_number")

        if self._is_valid_document_number(original_number):
            doc_num = str(original_number).strip()
        elif original_number:
            invalid_num = str(original_number).strip()
            if invalid_num:
                if cleaned_details:
                    if invalid_num.lower() not in cleaned_details.lower():
                        cleaned_details = f"{cleaned_details}; {invalid_num}"
                else:
                    cleaned_details = invalid_num

        return {
            "document_name": self._clean_document_name(cleaned_name),
            "document_number": doc_num,
            "document_date": cleaned_date,
            "document_copy_type": cleaned_copy,
            "additional_details": cleaned_details,
        }

    def _normalize_documents(self, documents: list) -> list[dict]:
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

                    "additional_details":
                        additional_details,
                }
            )

        return normalized

    def extract_documents(self, text: str) -> dict:
        if not text or not text.strip():
            raise ValueError("OCR text cannot be empty.")

        print("\n" + "=" * 55)
        print("DOCUMENT LIST EXTRACTION STARTED")
        print("=" * 55)
        print(f"📝 Input characters: {len(text)}")
        print(f"📝 Input words: {len(text.split())}")

        # Prompt construction
        start = time.perf_counter()
        prompt = self._build_prompt(text)
        print(f"⏱️ Prompt construction: {time.perf_counter() - start:.2f} seconds")
        print(f"📝 Prompt characters: {len(prompt)}")

        # --------------------------------------------------------
        # Ollama
        # --------------------------------------------------------

        start = time.perf_counter()

        response = self.ollama.generate(
            prompt
        )

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
        print("============================================")

        # --------------------------------------------------------
        # JSON parsing
        # --------------------------------------------------------

        start = time.perf_counter()

        data = self._parse_response(
            response
        )

        parsing_time = (
            time.perf_counter()
            - start
        )

        print(
            f"⏱️ JSON parsing: "
            f"{parsing_time:.2f} seconds"
        )

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
            "documents_prior_to_disbursal": prior_docs,
            "documents_post_disbursal": post_docs,
        }

        # Debug logs
        print("\n========== CLEAN DOCUMENT RESULT ==========")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        print("============================================")
        print(f"📋 Prior-disbursal documents: {len(prior_docs)}")
        print(f"📋 Post-disbursal documents: {len(post_docs)}")
        print("=" * 55)

        return result