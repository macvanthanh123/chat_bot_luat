from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.doc_parser import DocParser
from app.db.db_handler import PostgresHandler
from app.core.chunker import DocChunker
from app.core.gemini_client import GeminiClient
from app.core.search import SearchEngine
from app.utils.logger import logger
import os
from typing import Optional
import shutil
from pydantic import BaseModel


DOCX_DIR = os.path.join(os.getcwd(), "docx")
os.makedirs(DOCX_DIR, exist_ok=True)

db = PostgresHandler()
engine: Optional[SearchEngine] = None 
gemini = GeminiClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo và dọn dẹp tài nguyên (cách mới thay cho @app.on_event)."""
    logger.info("🚀 Khởi động dịch vụ API...")
    try:
        db.create_database()
        db.create_articles_table()
        db.create_chunks_table()
        app.state.engine = SearchEngine()
        logger.info("✅ Đã khởi tạo cơ sở dữ liệu và search engine.")
        yield
    except Exception as e:
        logger.exception(f"❌ Lỗi khởi tạo hệ thống: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi khởi động hệ thống")
    finally:
        logger.info("🛑 Đang tắt API...")


app = FastAPI(
    title="ChatBot Luật Việt Nam",
    description="Tra cứu và hỏi đáp điều luật theo tài liệu .docx",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # địa chỉ frontend của bạn
    allow_credentials=True,
    allow_methods=["*"],  # cho phép GET, POST, OPTIONS, ...
    allow_headers=["*"],  # cho phép headers từ frontend
)

@app.post("/upload/")
async def upload_docx(request: Request, file: UploadFile = File(...)):
    filename = file.filename
    saved_path = os.path.join(DOCX_DIR, filename)
    logger.info(f"📄 Nhận file upload: {filename}")

    try:
        # Lưu file tạm
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.debug(f"✅ Đã lưu file tại: {saved_path}")

        # Phân tích và lưu nội dung
        parser = DocParser(saved_path)
        data = parser.to_dict()
        logger.debug(f"📘 Đã phân tích tài liệu: {data.get('title', 'Không tiêu đề')}")

        article_id = db.insert_article(data)
        chunker = DocChunker(parser, doc_id=article_id)
        chunks = chunker.get_chunks()
        db.insert_chunks(article_id, chunks)
        logger.info(f"Đã lưu doc_id={article_id} với {len(chunks)} chunks.")
        request.app.state.engine.refresh()
        return JSONResponse({
            "message": "File đã được upload và xử lý thành công.",
            "filename": filename,
            "doc_id": article_id,
            "total_chunks": len(chunks)
        })

    except Exception as e:
        logger.exception(f"❌ Lỗi xử lý file '{filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(e)}")
@app.delete("/docs/{doc_id}")
async def delete_doc(doc_id: int):
    logger.info(f"🗑 Yêu cầu xóa doc_id={doc_id}")

    try:
        # Xóa trong database
        deleted = db.delete_article(doc_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu cần xóa")
        logger.info(f"🗑 Đã xóa tài liệu doc_id={doc_id}")
        return {"message": "Đã xóa tài liệu thành công", "doc_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Lỗi khi xóa doc_id={doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Không thể xóa tài liệu")
@app.get("/articles")
async def list_articles():
    try:
        articles = db.get_all_articles()
        return {"articles": articles}

    except Exception as e:
        logger.exception(f"❌ Lỗi khi lấy danh sách articles: {e}")
        raise HTTPException(status_code=500, detail="Không thể lấy danh sách tài liệu")

@app.get("/chunks/")
async def get_all_chunks(
    doc_id: Optional[int] = Query(None, description="ID tài liệu cần lấy chunks"),
    limit: Optional[int] = Query(None, description="Giới hạn số lượng chunks trả về")
):
    logger.info(f"📚 Truy vấn chunks | doc_id={doc_id} | limit={limit}")

    try:
        chunks = []
        if doc_id:
            chunks = db.fetch_chunks_by_doc_id(doc_id)
        else:
            for article in db.fetch_all_articles():
                chunks.extend(db.fetch_chunks_by_doc_id(article["id"]))

        if limit:
            chunks = chunks[:limit]

        return JSONResponse(chunks)

    except Exception as e:
        logger.exception(f"❌ Lỗi khi lấy chunks: {e}")
        raise HTTPException(status_code=500, detail="Không thể truy xuất dữ liệu")


@app.get("/search/vector/")
async def vector_search(request: Request, query: str = Query(...), top_k: int = Query(5, ge=1, le=50)):
    logger.info(f"🔍 Vector search: '{query}' | top_k={top_k}")
    try:
        engine: SearchEngine = request.app.state.engine
        results = engine.vector_search(query, top_k=top_k)
        return JSONResponse(results)
    except Exception as e:
        logger.exception(f"❌ Lỗi vector search: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi tìm kiếm vector")


@app.get("/search/keyword/")
async def keyword_search(request: Request, query: str = Query(...), top_k: int = Query(5, ge=1, le=50)):
    logger.info(f"🔍 Keyword search: '{query}' | top_k={top_k}")
    try:
        engine: SearchEngine = request.app.state.engine
        results = engine.keyword_search(query, top_k=top_k)
        return JSONResponse(results)
    except Exception as e:
        logger.exception(f"❌ Lỗi keyword search: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi tìm kiếm keyword")


@app.get("/search/hybrid/")
async def hybrid_search(
    request: Request,
    query: str = Query(...),
    top_k: int = Query(5, ge=1, le=50),
    alpha: float = Query(0.5, ge=0.0, le=1.0)
):
    logger.info(f"🔍 Hybrid search: '{query}' | top_k={top_k} | alpha={alpha}")
    try:
        engine: SearchEngine = request.app.state.engine
        results = engine.hybrid_search(query, top_k=top_k, alpha=alpha)
        return JSONResponse(results)
    except Exception as e:
        logger.exception(f"❌ Lỗi hybrid search: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi tìm kiếm hybrid")


class ChatRequest(BaseModel):
    query: str
    mode: str = "hybrid"
    top_k: int = 5
    alpha: float = 0.6
    model_llm: Optional[str] = None  # thêm biến model LLM
    prompt: Optional[str] = None

@app.post("/chat")
async def chat_with_gemini(request: Request, body: ChatRequest):
    query = body.query
    mode = body.mode
    top_k = body.top_k
    alpha = body.alpha
    model_llm = body.model_llm
    custom_prompt = body.prompt

    logger.info(f"💬 Chat: '{query}' | mode={mode} | top_k={top_k} | alpha={alpha} | model={model_llm}")

    try:
        engine: SearchEngine = request.app.state.engine

        # Chọn loại tìm kiếm
        if mode == "vector":
            search_results = engine.vector_search(query, top_k)
        elif mode == "keyword":
            search_results = engine.keyword_search(query, top_k)
        elif mode == "hybrid":
            search_results = engine.hybrid_search(query, top_k, alpha)
        else:
            raise HTTPException(status_code=400, detail="mode phải là: vector, keyword hoặc hybrid")

        # Tạo prompt: nếu có prompt từ request thì dùng, ngược lại build từ gemini
        
        prompt = gemini.build_prompt(query, search_results,custom_instructions=custom_prompt)

        # Chat với LLM: nếu có model_llm thì dùng model đó
        if model_llm:
            response = gemini.chat(prompt, model_llm=model_llm)
        else:
            response = gemini.chat(prompt)

        return JSONResponse({
            "query": query,
            "mode": mode,
            "top_k": top_k,
            "alpha": alpha if mode == "hybrid" else None,
            "model_llm": model_llm,
            "prompt": prompt,
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
        })
    except Exception as e:
        logger.exception(f"❌ Lỗi khi chat: {e}")
        raise HTTPException(status_code=500, detail="Lỗi xử lý câu hỏi")