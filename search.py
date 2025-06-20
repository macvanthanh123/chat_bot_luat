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
        results = []

        for chunk in self.all_chunks:
            vector = chunk.get("vector")
            if not vector:
                continue
            doc_vec = np.array(vector).reshape(1, -1)
            score = cosine_similarity(query_vec, doc_vec)[0][0]
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

        for chunk in self.all_chunks:
            title_norm = self._normalize(chunk["title"])
            if query_norm in title_norm:
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
                if (chunk["doc_id"], chunk["chunk_id"]) in {(r["doc_id"], r["chunk_id"]) for r in results}:
                    continue 
                content_norm = self._normalize(chunk["content"])
                if query_norm in content_norm:
                    results.append({
                        "doc_id": chunk["doc_id"],
                        "chunk_id": chunk["chunk_id"],
                        "title": chunk["title"],
                        "content": chunk["content"],
                        "score": 0.9,
                        "type": "keyword"
                    })

        if len(results) < top_k:
            keywords = query_norm.split()
            for chunk in self.all_chunks:
                key = (chunk["doc_id"], chunk["chunk_id"])
                if key in {(r["doc_id"], r["chunk_id"]) for r in results}:
                    continue
                text = f"{chunk['title']} {chunk['content']}"
                text_norm = self._normalize(text)
                match_score = sum(1 for kw in keywords if kw in text_norm) / len(keywords)
                if match_score >= 0.4:
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

        kw_dict = {}
        for r in kw_results:
            key = (r["doc_id"], r["chunk_id"])
            title_norm = self._normalize(r["title"])
            if query_norm in title_norm:
                r["score"] = 1.0
            elif query_norm in self._normalize(r["content"]):
                r["score"] = 0.9
            kw_dict[key] = r

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
                    "score": r["score"],
                    "type": "hybrid"
                })

        return sorted(hybrid, key=lambda x: x["score"], reverse=True)[:top_k]
