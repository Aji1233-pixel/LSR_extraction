import sys
import os

# Ensure UTF-8 output so emoji/logs don't crash on
# Windows consoles that default to cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ["PYTHONIOENCODING"] = "utf-8"

from fastapi import FastAPI

from backend.routes.document import router as document_router


app = FastAPI(
    title="Document Extraction API",
    version="1.0.0",
)


app.include_router(document_router)


@app.get("/")
def root():
    return {
        "message": "Document Extraction API is running."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }