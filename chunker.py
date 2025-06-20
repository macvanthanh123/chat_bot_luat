import re
import json
from doc_parser import DocParser
from sentence_transformers import SentenceTransformer


class DocChunker:
    def __init__(self, parser: DocParser, doc_id: int):
        self.paragraphs = parser.paragraphs
        self.doc_id = doc_id
        self.embed_model = SentenceTransformer('all-mpnet-base-v2')
        self.chunks = self._chunk_by_article()

    def _chunk_by_article(self):
        chunks = []
        current_chunk = {"title": "", "content": []}

        for para in self.paragraphs:
            if re.match(r"^(Điều|ĐIỀU)\s+\d+", para):
                if current_chunk["title"]:
                    chunks.append(current_chunk)
                    current_chunk = {"title": "", "content": []}
                current_chunk["title"] = para
            else:
                current_chunk["content"].append(para)

        if current_chunk["title"]:
            chunks.append(current_chunk)

        result = []
        for idx, chunk in enumerate(chunks, start=1):
            content = chunk["title"] + "\n" + "\n".join(chunk["content"])
            embedding = self.embed_model.encode(content).tolist()

            result.append({
                "doc_id": self.doc_id,
                "chunk_id": idx,
                "title": chunk["title"],
                "content": content,
                "vector": embedding
            })

        return result

    def save_to_json(self, filename="chunks_by_article.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)

    def get_chunks(self):
        return self.chunks
