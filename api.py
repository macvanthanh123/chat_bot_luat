from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from doc_parser import DocParser
from db_handler import PostgresHandler
from chunker import DocChunker
from gemini_client import GeminiClient
from search import SearchEngine
import os
import tempfile
import uuid

app = FastAPI(
    title="ChatBot Luật Việt Nam",
    description="Tra cứu và hỏi đáp điều luật theo tài liệu .docx",
    version="1.0.0"
)

db = PostgresHandler()
engine = None
gemini = GeminiClient()  
DOCX_DIR = os.path.join(os.getcwd(), "docx")

@app.on_event("startup")
def startup():
    db.create_database()
    db.create_articles_table()
    db.create_chunks_table()
    global engine
    engine = SearchEngine()


@app.post("/upload/")
async def upload_docx(file: UploadFile = File(...)):
    filename = file.filename
    saved_path = os.path.join(DOCX_DIR, filename)

    try:
        with open(saved_path, "wb") as f:
            f.write(await file.read())

        parser = DocParser(saved_path)
        data = parser.to_dict()

        article_id = db.insert_article(data)
        chunker = DocChunker(parser, doc_id=article_id)
        chunks = chunker.get_chunks()
        db.insert_chunks(article_id, chunks)

        return {
            "message": "File đã được upload, xử lý và lưu vào thư mục",
            "filename": filename,
            "doc_id": article_id,
            "total_chunks": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(e)}")

@app.get("/chunks/")
def get_all_chunks(doc_id: int = None, limit: int = None):
    """
    Trả về các chunk, có thể lọc theo doc_id và giới hạn số lượng bằng limit.
    """
    if doc_id is not None:
        chunks = db.fetch_chunks_by_doc_id(doc_id)
    else:
        articles = db.fetch_all_articles()
        chunks = []
        for article in articles:
            chunks.extend(db.fetch_chunks_by_doc_id(article["id"]))
    if limit is not None:
        chunks = chunks[:limit]
    return JSONResponse(chunks)

@app.get("/search/vector/")
def vector_search(query: str = Query(...), top_k: int = 5):
    results = engine.vector_search(query, top_k=top_k)
    return JSONResponse(results)


@app.get("/search/keyword/")
def keyword_search(query: str = Query(...), top_k: int = 5):
    results = engine.keyword_search(query, top_k=top_k)
    return JSONResponse(results)


@app.get("/search/hybrid/")
def hybrid_search(query: str = Query(...), top_k: int = 5, alpha: float = 0.5):
    results = engine.hybrid_search(query, top_k=top_k, alpha=alpha)
    return JSONResponse(results)


@app.get("/chat/")
def chat_with_gemini(
    query: str = Query(..., description="Câu hỏi của người dùng"),
    mode: str = Query("hybrid", description="Phương pháp tìm kiếm: vector | keyword | hybrid"),
    top_k: int = Query(5, ge=1, le=20),
    alpha: float = Query(0.6, ge=0.0, le=1.0)
):
    if mode == "vector":
        search_results = engine.vector_search(query, top_k=top_k)
    elif mode == "keyword":
        search_results = engine.keyword_search(query, top_k=top_k)
    elif mode == "hybrid":
        search_results = engine.hybrid_search(query, top_k=top_k, alpha=alpha)
    else:
        raise HTTPException(status_code=400, detail="mode phải là: vector, keyword hoặc hybrid")

    prompt = gemini.build_prompt(query, search_results)  
    response = gemini.chat(prompt)

    return {
        "query": query,
        "mode": mode,
        "top_k": top_k,
        "alpha": alpha if mode == "hybrid" else None,
        "answer": response,
        "sources": [
            {
                "doc_id": r["doc_id"],
                "chunk_id": r["chunk_id"],
                "title": r["title"],
                "content": r["content"],
                "score": round(r["score"], 4),
                "type": r["type"]
            } for r in search_results
        ]
    }
