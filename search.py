import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from db_handler import PostgresHandler
from logger import logger  

class SearchEngine:
    def __init__(self):
        logger.info("Khởi tạo SearchEngine...")
        self.db = PostgresHandler()
        self.embed_model = SentenceTransformer("all-mpnet-base-v2")

        self.all_chunks = []
        articles = self.db.fetch_all_articles()
        logger.info("Đã load {} bài viết từ database", len(articles))

        for article in articles:
            chunks = self.db.fetch_chunks_by_doc_id(article["id"])
            logger.debug("Bài viết id={} có {} chunks", article["id"], len(chunks))
            self.all_chunks.extend(chunks)

        logger.info("Tổng số chunks được nạp vào bộ tìm kiếm: {}", len(self.all_chunks))

    def encode_query(self, query: str):
        try:
            embedding = self.embed_model.encode(query).reshape(1, -1)
            logger.debug("Vector hóa truy vấn thành công")
            return embedding
        except Exception as e:
            logger.exception("Lỗi khi vector hóa truy vấn: {}", e)
            return None

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^\w\s]", "", text.lower()).strip()

    def vector_search(self, query: str, top_k=5):
        logger.info("Thực hiện vector search: query='{}' | top_k={}", query, top_k)
        query_vec = self.encode_query(query)
        if query_vec is None:
            return []

        query_vec = np.array(query_vec).reshape(1, -1)
        query_vec = query_vec / np.linalg.norm(query_vec)

        results = []
        for chunk in self.all_chunks:
            vector = chunk.get("vector")
            if not vector or not isinstance(vector, list):
                continue

            try:
                doc_vec = np.array(vector)
                doc_vec = doc_vec / np.linalg.norm(doc_vec)
                score = float(np.dot(query_vec, doc_vec))
                results.append({
                    "doc_id": chunk["doc_id"],
                    "chunk_id": chunk["chunk_id"],
                    "title": chunk["title"],
                    "content": chunk["markdown"],
                    "score": score,
                    "type": "vector"
                })
            except Exception as e:
                logger.warning("Lỗi khi tính cosine: chunk_id={} | {}", chunk.get("chunk_id"), e)

        logger.info("Vector search trả về {} kết quả", len(results))
        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def keyword_search(self, query: str, top_k: int = 5):
        logger.info("Thực hiện keyword search: query='{}' | top_k={}", query, top_k)
        results = []
        query_norm = self._normalize(query)
        dieu_match = re.search(r"điều\s+(\d+)", query_norm)

        if dieu_match:
            dieu_query = f"{dieu_match.group(0)}"
            for chunk in self.all_chunks:
                content_norm = self._normalize(chunk["markdown"])
                if dieu_query in content_norm:
                    results.append({
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "title": chunk["title"],
                        "content": chunk["markdown"],
                        "score": 1.0,
                        "type": "keyword"
                    })
        if len(results) < top_k:
            for chunk in self.all_chunks:
                content_norm = self._normalize(chunk["markdown"])
                if query_norm in content_norm:
                    key = (chunk["doc_id"], chunk["chunk_id"])
                    if key not in {(r["doc_id"], r["chunk_id"]) for r in results}:
                        results.append({
                            "doc_id": chunk["doc_id"],
                            "chunk_id": chunk["chunk_id"],
                            "title": chunk["title"],
                            "content": chunk["markdown"],
                            "score": 1.0,
                            "type": "keyword"
                        })

        if len(results) < top_k:
            stop_words = {
                "tôi", "là", "cho", "hay", "xin", "biết", "giúp", "với", "làm", "có", "bạn",
                "của", "ở", "và", "hoặc", "nhé", "thì", "đó", "này", "nào", "cái", "vậy", "ra",
                "đi", "được", "sao", "ai", "đâu", "đây", "gì", "hả", "không", "như", "nha", "nhưng"
            }

            keywords = [kw for kw in query_norm.split() if kw not in stop_words]
            for chunk in self.all_chunks:
                key = (chunk["doc_id"], chunk["chunk_id"])
                if key in {(r["doc_id"], r["chunk_id"]) for r in results}:
                    continue
                content_norm = self._normalize(chunk["markdown"])
                match_score = sum(1 for kw in keywords if kw in content_norm) / max(1, len(keywords))
                if match_score >= 0.2:
                    results.append({
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "title": chunk["title"],
                        "content": chunk["markdown"],
                        "score": round(match_score, 2),
                        "type": "keyword"
                    })

        logger.info("Keyword search trả về {} kết quả", len(results))
        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def hybrid_search(self, query: str, top_k=5, alpha=0.6):
        logger.info("Thực hiện hybrid search: query='{}' | top_k={} | alpha={}", query, top_k, alpha)

        vec_results = self.vector_search(query, top_k=100)
        kw_results = self.keyword_search(query, top_k=100)

        kw_dict = {
            (r["doc_id"], r["chunk_id"]): r
            for r in kw_results
        }

        hybrid = []
        seen_keys = set()

        for r in vec_results:
            key = (r["doc_id"], r["chunk_id"])
            kw_score = kw_dict[key]["score"] if key in kw_dict else 0.0
            hybrid_score = alpha * r["score"] + (1 - alpha) * kw_score

            hybrid.append({
                "doc_id": r["doc_id"],
                "chunk_id": r["chunk_id"],
                "title": r["title"],
                "content": r["content"],
                "score": round(hybrid_score, 4),
                "type": "hybrid"
            })
            seen_keys.add(key)

        for key, r in kw_dict.items():
            if key not in seen_keys:
                hybrid.append({
                    "doc_id": r["doc_id"],
                    "chunk_id": r["chunk_id"],
                    "title": r["title"],
                    "content": r["content"],
                    "score": round((1 - alpha) * r["score"], 4),
                    "type": "hybrid"
                })

        logger.info("Hybrid search trả về {} kết quả", len(hybrid))
        return sorted(hybrid, key=lambda x: x["score"], reverse=True)[:top_k]
