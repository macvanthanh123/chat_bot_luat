import requests
from bs4 import BeautifulSoup
import json
import sys
import os
sys.path.append(os.path.abspath(r"C:\Users\MAC VAN THANH\Desktop\BTL_xlnntn\chat_bot_luat"))
from db_handler import PostgresHandler
import re
from sentence_transformers import SentenceTransformer

db = PostgresHandler()
class WebChunker:
    def __init__(self, data_dict: dict, doc_id: int):
        self.data = data_dict
        self.doc_id = doc_id
        self.embed_model = SentenceTransformer('all-mpnet-base-v2')

    def chunk_by_article(self):
        chunks = []
        current_chunk = {"title": "", "markdown": []}

        paragraphs = self.data.get("markdown", "").split("\n\n")
        if not paragraphs or len(paragraphs) < 2:
            paragraphs = self.data.get("text", "").split("\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if re.match(r"(#+\s*)?Điều\s+\d+", para):
                if current_chunk["title"]:
                    chunks.append(current_chunk)
                    current_chunk = {"title": "", "markdown": []}
                current_chunk["title"] = para
            else:
                current_chunk["markdown"].append(para)

        if current_chunk["title"]:
            chunks.append(current_chunk)


        result = []
        for idx, chunk in enumerate(chunks, start=1):
            markdown = chunk["title"] + "\n" + "\n".join(chunk["markdown"])
            try:
                embedding = self.embed_model.encode(markdown).tolist()
            except Exception as e:
                embedding = []

            result.append({
                "doc_id": self.doc_id,
                "chunk_id": idx,
                "title": chunk["title"],
                "content": markdown,
                "vector": embedding
            })

        return result
    
url = "https://luatchiminh.com/bo-luat-dan-su-2015.html"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
images= []
title_tag = soup.find("title")
title = title_tag.text.strip() if title_tag else ""
date = ""
table = soup.find("table")
if table:
    i_tags = table.find_all("i")
    for i_tag in i_tags:
        if "ngày" in i_tag.text:
            date = i_tag.get_text(strip=True)
            break

content_div = soup.find("div", class_="content")
text_parts = []
markdown_parts = []

if content_div:
    for tag in content_div.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
        text = tag.get_text(strip=True)
        if not text:
            continue
        text_parts.append(text)

        if tag.name.startswith("h"):
            markdown_parts.append(f"{'#' * int(tag.name[1])} {text}")
        elif tag.name == "li":
            markdown_parts.append(f"- {text}")
        else:
            markdown_parts.append(text)

full_text = "\n".join(text_parts)
markdown = "\n\n".join(markdown_parts)

data_list = {
    "url": url,
    "title": title,
    "date": date,
    "text": full_text,
    "markdown": markdown,
    "images": images
}
article_id = db.insert_article(data_list)
chunker = WebChunker(data_list, doc_id=article_id)
chunks = chunker.chunk_by_article()
db.insert_chunks(article_id, chunks)



