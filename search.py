import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from db_handler import PostgresHandler
import re


class SearchEngine:
    def __init__(self):
        self.db = PostgresHandler()
        self.embed_model = SentenceTransformer("all-mpnet-base-v2")

        self.all_chunks = []
        for article in self.db.fetch_all_articles():
            chunks = self.db.fetch_chunks_by_doc_id(article["id"])
            self.all_chunks.extend(chunks)

    def encode_query(self, query: str):
        return self.embed_model.encode(query).reshape(1, -1)

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^\w\s]", "", text.lower()).strip()

    def vector_search(self, query: str, top_k=5):
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

            doc_vec = np.array(vector)
            doc_vec = doc_vec / np.linalg.norm(doc_vec)

            score = float(np.dot(query_vec, doc_vec))
            results.append({
                "doc_id": chunk["doc_id"],
                "chunk_id": chunk["chunk_id"],
                "title": chunk["title"],
                "content": chunk["content"],
                "score": score,
                "type": "vector"
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]


    def keyword_search(self, query: str, top_k: int = 5):
        results = []
        query_norm = self._normalize(query)
        print('query_norm:', query_norm)
        dieu_match = re.search(r"điều\s+(\d+)", query_norm)
        if dieu_match:
            dieu_query = f"{dieu_match.group(0)}"
            print('dieu_query:', dieu_query)
            for chunk in self.all_chunks:
                content_norm = self._normalize(chunk["content"])
                if dieu_query in content_norm:
                    results.append({
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "title": chunk["title"],
                        "content": chunk["content"],
                        "score": 1.0,
                        "type": "keyword"
                    })
        if len(results) < top_k:
            for chunk in self.all_chunks:
                content_norm = self._normalize(chunk["content"])
                if query_norm in content_norm:
                    key = (chunk["doc_id"], chunk["chunk_id"])
                    if key not in {(r["doc_id"], r["chunk_id"]) for r in results}:
                        results.append({
                            "doc_id": chunk["doc_id"],
                            "chunk_id": chunk["chunk_id"],
                            "title": chunk["title"],
                            "content": chunk["content"],
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
                content_norm = self._normalize(chunk["content"])
                match_score = sum(1 for kw in keywords if kw in content_norm) / max(1, len(keywords))
                if match_score >= 0.2:
                    results.append({
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "title": chunk["title"],
                        "content": chunk["content"],
                        "score": round(match_score, 2),
                        "type": "keyword"
                    })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]


    def hybrid_search(self, query: str, top_k=5, alpha=0.6):
        query_norm = self._normalize(query)

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

        return sorted(hybrid, key=lambda x: x["score"], reverse=True)[:top_k]

