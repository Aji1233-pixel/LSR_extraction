import json
import re
import time


class DocumentExtractor:
    """
    Extracts documents required before and after loan disbursal.

    Output structure for every document:

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

For every document return EXACTLY these fields:

- document_name
- document_number
- document_date
- document_copy_type
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


EXAMPLE 1

Input:

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


EXAMPLE 2

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


EXAMPLE 3

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


EXAMPLE 4

Input:

Property Tax Receipt in the name of Vasantha Kumar

Output:

{{
    "document_name": "Property Tax Receipt",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Xerox",
    "additional_details": "in the name of Vasantha Kumar"
}}


Required JSON structure:

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


============================================================
DOCUMENT TEXT
============================================================

{text}
""".strip()

    # ============================================================
    # JSON PARSING
    # ============================================================

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
        # Ollama (with retry logic for empty responses)
        # --------------------------------------------------------

        start = time.perf_counter()

        max_retries = 3
        response = None

        for attempt in range(max_retries):
            response = self.ollama.generate(prompt)
            if response and response.strip():
                break
            print(f"⚠️ LLM returned empty response (attempt {attempt + 1}/{max_retries}), retrying...")
            time.sleep(1)

        if not response or not response.strip():
            raise RuntimeError(
                f"LLM returned empty response after {max_retries} attempts."
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

        print(
            "============================================"
        )

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