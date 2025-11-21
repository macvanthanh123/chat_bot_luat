import re
import json
from app.core.doc_parser import DocParser
from sentence_transformers import SentenceTransformer
from app.utils.logger import logger  

class DocChunker:
    def __init__(self, parser: DocParser, doc_id: int):
        self.paragraphs = parser._convert_to_markdown_structured().split('\n')
        self.doc_id = doc_id
        self.embed_model = SentenceTransformer('AITeamVN/Vietnamese_Embedding')
        self.embed_model.max_seq_length = 512
        logger.info("Khởi tạo DocChunker cho doc_id={}", doc_id)
        self.chunks = self._chunk_by_article()

    def _read_markdow(self):
        logger.debug("Nội dung markdown raw:\n{}", self.paragraphs)

    def _chunk_by_article(self):
        logger.info("Bắt đầu chia văn bản theo Điều luật...")
        chunks = []
        current_chunk = {"title": "", "markdown": []}

        for para in self.paragraphs:
            if re.match(r"(?=##?\s*Điều\s+\d+)", para):
                if current_chunk["title"]:
                    chunks.append(current_chunk)
                    current_chunk = {"title": "", "markdown": []}
                current_chunk["title"] = para
            else:
                current_chunk["markdown"].append(para)

        if current_chunk["title"]:
            chunks.append(current_chunk)

        logger.info("Tổng số chunks được tạo: {}", len(chunks))

        result = []
        for idx, chunk in enumerate(chunks, start=1):
            markdown = chunk["title"] + "\n" + "\n".join(chunk["markdown"])
            try:
                embedding = self.embed_model.encode(markdown).tolist()
            except Exception as e:
                logger.exception("Lỗi khi encode embedding cho chunk_id {}: {}", idx, e)
                embedding = []

            result.append({
                "doc_id": self.doc_id,
                "chunk_id": idx,
                "title": chunk["title"],
                "markdown": markdown,
                "vector": embedding
            })

            logger.debug("Chunk {} - {} ký tự", idx, len(markdown))

        return result

    def save_to_json(self, filename="chunks_by_article.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=4)
            logger.info("Đã lưu chunks vào file {}", filename)
        except Exception as e:
            logger.exception("Lỗi khi lưu chunks vào file {}: {}", filename, e)

    def get_chunks(self):
        logger.debug("Trả về danh sách {} chunks", len(self.chunks))
        return self.chunks
