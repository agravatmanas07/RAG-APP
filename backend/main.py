"""
Production RAG Application — FastAPI + ChromaDB
Author: Manas Agravat | AI & Data Engineer
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import io
import uuid
import os
import anthropic
from typing import Optional

app = FastAPI(
    title="Production RAG API",
    description="RAG application for CSV/Excel data using ChromaDB + Claude",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ChromaDB Setup ────────────────────────────────────────────────────────────
chroma_client = chromadb.Client()
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

collections: dict = {}  # store_id -> collection

# ── Models ────────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    store_id: str
    question: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: list
    store_id: str

# ── Helpers ───────────────────────────────────────────────────────────────────
def dataframe_to_chunks(df: pd.DataFrame) -> list[str]:
    """Convert each row of a DataFrame into a text chunk."""
    chunks = []
    cols = df.columns.tolist()
    for _, row in df.iterrows():
        parts = [f"{col}: {row[col]}" for col in cols if pd.notna(row[col])]
        chunk = " | ".join(parts)
        if chunk.strip():
            chunks.append(chunk)
    return chunks

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "message": "RAG API is running 🚀"}

@app.get("/stores")
def list_stores():
    """List all uploaded data stores."""
    return {"stores": list(collections.keys())}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or Excel file and index it into ChromaDB."""
    filename = file.filename or ""
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported.")

    contents = await file.read()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

    # Clean up
    df.dropna(how="all", inplace=True)
    df.fillna("", inplace=True)

    chunks = dataframe_to_chunks(df)
    if not chunks:
        raise HTTPException(status_code=422, detail="No usable data found in file.")

    store_id = str(uuid.uuid4())[:8]
    collection = chroma_client.create_collection(
        name=f"store_{store_id}",
        embedding_function=embedding_fn
    )
    ids = [f"doc_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids)
    collections[store_id] = collection

    return {
        "store_id": store_id,
        "filename": filename,
        "rows_indexed": len(chunks),
        "columns": df.columns.tolist(),
        "preview": chunks[:3]
    }

@app.post("/query", response_model=QueryResponse)
async def query_rag(req: QueryRequest):
    """Query the RAG system and get an AI-generated answer."""
    if req.store_id not in collections:
        raise HTTPException(status_code=404, detail="Store not found. Please upload a file first.")

    collection = collections[req.store_id]

    # Retrieve relevant chunks
    results = collection.query(
        query_texts=[req.question],
        n_results=min(req.top_k, collection.count())
    )
    docs = results["documents"][0] if results["documents"] else []

    if not docs:
        return QueryResponse(
            answer="No relevant data found for your question.",
            sources=[],
            store_id=req.store_id
        )

    # Build context
    context = "\n".join([f"- {d}" for d in docs])
    prompt = f"""You are a data analyst assistant. Use ONLY the context below to answer the question.
Be concise, accurate, and structured. If the answer is not in the context, say so.

Context:
{context}

Question: {req.question}

Answer:"""

    # Call Claude API
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = message.content[0].text
    except Exception as e:
        # Fallback: return raw context if API fails
        answer = f"Based on the data:\n{context}"

    return QueryResponse(
        answer=answer,
        sources=docs,
        store_id=req.store_id
    )

@app.delete("/stores/{store_id}")
def delete_store(store_id: str):
    """Delete a data store."""
    if store_id not in collections:
        raise HTTPException(status_code=404, detail="Store not found.")
    chroma_client.delete_collection(f"store_{store_id}")
    del collections[store_id]
    return {"message": f"Store {store_id} deleted successfully."}
