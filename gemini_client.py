import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-1.5-flash")

    def chat(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[ERROR] {str(e)}"

    def classify_query(self, query: str) -> str:
        normalized = query.lower()
        greetings = ["chào", "xin chào", "hello", "hi", "yo", "bạn khỏe không"]
        personal = ["bạn là ai", "giới thiệu", "tên bạn", "chức năng", "làm gì", "giúp gì"]
        legal_keywords = ["điều", "luật", "quy định", "thuế", "pháp luật", "trách nhiệm", "nghĩa vụ"]

        if any(word in normalized for word in greetings + personal):
            return "greeting"
        elif any(word in normalized for word in legal_keywords):
            return "legal"
        else:
            return "general"

    def build_prompt(self, query: str, search_results: list) -> str:
        category = self.classify_query(query)

        if category == "greeting":
            return f"""
Bạn là một trợ lý pháp lý thân thiện.

Người dùng hỏi:
\"{query}\"

👉 Hãy chào hỏi, giới thiệu bản thân một cách ngắn gọn, thân thiện và thể hiện rằng bạn có thể hỗ trợ tra cứu điều luật khi cần.
""".strip()

        elif category == "legal" and search_results:
            context = "\n\n".join(f"{chunk['content']}" for chunk in search_results)
            return f"""
Bạn là một trợ lý pháp luật thông minh.

Câu hỏi:
\"{query}\"

Các đoạn luật liên quan:
{context}

👉 Trả lời đúng nội dung luật, rõ ràng, dễ hiểu. Không suy đoán, không sáng tạo.  
❗ Nếu nội dung chưa đủ, hãy nói: "Tôi chưa có đủ thông tin để trả lời chính xác."
""".strip()

        elif category == "legal" and not search_results:
            return f"""
Bạn là một trợ lý pháp luật thông minh.

Câu hỏi:
\"{query}\"

👉 Rất tiếc, hiện tại tôi không tìm thấy điều luật nào liên quan đến câu hỏi này trong dữ liệu của bạn.  
Hãy thử đặt lại câu hỏi cụ thể hơn hoặc tải thêm tài liệu luật liên quan.
""".strip()

        else:  # general
            return f"""
Bạn là một trợ lý thông minh, thân thiện.

Người dùng hỏi:
\"{query}\"

👉 Trả lời tự nhiên, gần gũi như một trợ lý thông minh. Nếu không rõ câu hỏi, hãy gợi ý người dùng hỏi về điều luật hoặc chủ đề cụ thể hơn.
""".strip()

    def build_strict_prompt(self, query: str, chunk: dict) -> str:
        title = chunk.get("title", "")
        content = chunk.get("content", "")

        return f"""
Bạn là một trợ lý pháp lý thông minh, chuyên hỗ trợ trích xuất chính xác nội dung từ văn bản pháp luật.

Câu hỏi:
\"{query}\"

Nội dung điều luật:
📘 {title}
{content}

👉 Hãy chỉ sử dụng nội dung trên để trả lời một cách thân thiện.  
Không được phỏng đoán, không sáng tạo.  
Nếu câu trả lời không nằm trong điều luật này, hãy nói: "Tôi không có đủ thông tin trong điều luật này để trả lời chính xác."
""".strip()
