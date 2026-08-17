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