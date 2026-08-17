import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/api/extract"


st.set_page_config(
    page_title="Document Extraction",
    page_icon="📄",
    layout="wide",
)


st.title("📄 Document Extraction System")

st.write(
    "Upload an LSR document to extract the required information."
)


uploaded_file = st.file_uploader(
    "Upload Document",
    type=[
        "pdf",
        "jpg",
        "jpeg",
        "png",
        "tif",
        "tiff",
    ],
)


if uploaded_file is not None:

    st.info(
        f"Selected file: {uploaded_file.name}"
    )

    if st.button(
        "Extract Information",
        type="primary",
    ):

        with st.spinner(
            "Processing document..."
        ):

            try:
                response = requests.post(
                    API_URL,
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    },
                    timeout=300,
                )

                if response.status_code == 200:

                    result = response.json()

                    st.success(
                        "Document processed successfully."
                    )

                    extracted_fields = result[
                        "extracted_fields"
                    ]

                    st.subheader(
                        "Extracted Information"
                    )

                    for field, value in extracted_fields.items():

                        display_name = field.replace(
                            "_",
                            " "
                        ).title()

                        if value is None:
                            value = "Not found"

                        st.write(
                            f"**{display_name}:** {value}"
                        )

                else:

                    try:
                        error = response.json()
                        message = error.get(
                            "detail",
                            "Unknown error"
                        )
                    except Exception:
                        message = response.text

                    st.error(
                        f"Extraction failed: {message}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to FastAPI. "
                    "Make sure the backend is running."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The document processing request timed out."
                )

            except Exception as exc:

                st.error(
                    f"Unexpected error: {exc}"
                )