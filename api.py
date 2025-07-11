from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from doc_parser import DocParser
from db_handler import PostgresHandler
from chunker import DocChunker
from gemini_client import GeminiClient
from search import SearchEngine
from logger import logger  
import os

app = FastAPI(
    title="ChatBot Luật Việt Nam",
    description="Tra cứu và hỏi đáp điều luật theo tài liệu .docx",
    version="1.0.0"
)

db = PostgresHandler()
engine = None
gemini = GeminiClient()
DOCX_DIR = os.path.join(os.getcwd(), "docx")
os.makedirs(DOCX_DIR, exist_ok=True)


@app.on_event("startup")
def startup():
    logger.info("Khởi động dịch vụ API...")
    try:
        db.create_database()
        db.create_articles_table()
        db.create_chunks_table()
        global engine
        engine = SearchEngine()
        logger.info("Đã khởi tạo cơ sở dữ liệu và search engine")
    except Exception as e:
        logger.exception("Lỗi khởi tạo hệ thống: {}", e)
        raise HTTPException(status_code=500, detail="Lỗi khi khởi động hệ thống")


@app.post("/upload/")
async def upload_docx(file: UploadFile = File(...)):
    filename = file.filename
    saved_path = os.path.join(DOCX_DIR, filename)
    logger.info("Nhận file upload: {}", filename)

    try:
        with open(saved_path, "wb") as f:
            f.write(await file.read())
        logger.debug("Đã lưu file vào: {}", saved_path)

        parser = DocParser(saved_path)
        data = parser.to_dict()
        logger.debug("Đã phân tích tài liệu: {}", data["title"])

        article_id = db.insert_article(data)
        logger.info("Đã lưu bài viết với doc_id: {}", article_id)

        chunker = DocChunker(parser, doc_id=article_id)
        chunks = chunker.get_chunks()
        db.insert_chunks(article_id, chunks)
        logger.info("Đã tạo {} chunk từ tài liệu", len(chunks))

        return {
            "message": "File đã được upload, xử lý và lưu vào thư mục",
            "filename": filename,
            "doc_id": article_id,
            "total_chunks": len(chunks)
        }

    except Exception as e:
        logger.exception("Lỗi xử lý file '{}': {}", filename, e)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(e)}")


@app.get("/chunks/")
def get_all_chunks(doc_id: int = None, limit: int = None):
    logger.info("Truy vấn danh sách chunks | doc_id={} | limit={}", doc_id, limit)

    try:
        if doc_id is not None:
            chunks = db.fetch_chunks_by_doc_id(doc_id)
        else:
            articles = db.fetch_all_articles()
            chunks = []
            for article in articles:
                chunks.extend(db.fetch_chunks_by_doc_id(article["id"]))

        if limit is not None:
            chunks = chunks[:limit]

        logger.debug("Trả về {} chunks", len(chunks))
        return JSONResponse(chunks)
    except Exception as e:
        logger.exception("Lỗi khi lấy chunks: {}", e)
        raise HTTPException(status_code=500, detail="Không thể truy xuất dữ liệu")


@app.get("/search/vector/")
def vector_search(query: str = Query(...), top_k: int = 5):
    logger.info("🔍 Vector search: query='{}' | top_k={}", query, top_k)
    try:
        results = engine.vector_search(query, top_k=top_k)
        logger.debug("Vector search trả về {} kết quả", len(results))
        return JSONResponse(results)
    except Exception as e:
        logger.exception("Lỗi vector search: {}", e)
        raise HTTPException(status_code=500, detail="Lỗi khi tìm kiếm vector")


@app.get("/search/keyword/")
def keyword_search(query: str = Query(...), top_k: int = 5):
    logger.info("🔍 Keyword search: query='{}' | top_k={}", query, top_k)
    try:
        results = engine.keyword_search(query, top_k=top_k)
        logger.debug("Keyword search trả về {} kết quả", len(results))
        return JSONResponse(results)
    except Exception as e:
        logger.exception("Lỗi keyword search: {}", e)
        raise HTTPException(status_code=500, detail="Lỗi khi tìm kiếm keyword")


@app.get("/search/hybrid/")
def hybrid_search(query: str = Query(...), top_k: int = 5, alpha: float = 0.5):
    logger.info("🔍 Hybrid search: query='{}' | top_k={} | alpha={}", query, top_k, alpha)
    try:
        results = engine.hybrid_search(query, top_k=top_k, alpha=alpha)
        logger.debug("Hybrid search trả về {} kết quả", len(results))
        return JSONResponse(results)
    except Exception as e:
        logger.exception("Lỗi hybrid search: {}", e)
        raise HTTPException(status_code=500, detail="Lỗi khi tìm kiếm hybrid")


@app.get("/chat/")
def chat_with_gemini(
    query: str = Query(..., description="Câu hỏi của người dùng"),
    mode: str = Query("hybrid", description="Phương pháp tìm kiếm: vector | keyword | hybrid"),
    top_k: int = Query(5, ge=1, le=20),
    alpha: float = Query(0.6, ge=0.0, le=1.0)
):
    logger.info("Chat: query='{}' | mode={} | top_k={} | alpha={}", query, mode, top_k, alpha)

    try:
        if mode == "vector":
            search_results = engine.vector_search(query, top_k=top_k)
        elif mode == "keyword":
            search_results = engine.keyword_search(query, top_k=top_k)
        elif mode == "hybrid":
            search_results = engine.hybrid_search(query, top_k=top_k, alpha=alpha)
        else:
            logger.warning("Sai mode truy vấn: {}", mode)
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

    except Exception as e:
        logger.exception("Lỗi khi xử lý chat: {}", e)
        raise HTTPException(status_code=500, detail="Lỗi trong quá trình xử lý câu hỏi")
