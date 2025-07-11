import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from logger import logger  

load_dotenv()

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error(" Không tìm thấy GEMINI_API_KEY trong file .env")
            raise ValueError("Missing GEMINI_API_KEY in .env")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("models/gemini-1.5-flash")
        logger.info("Đã khởi tạo GeminiClient với model gemini-1.5-flash")

    def chat(self, prompt: str) -> str:
        try:
            short_prompt = prompt[:100].replace("\n", " ") + "..." if len(prompt) > 100 else prompt
            logger.debug(" Gửi prompt tới Gemini: {}", short_prompt)

            response = self.model.generate_content(prompt)
            logger.debug(" Đã nhận phản hồi từ Gemini")
            return response.text

        except Exception as e:
            logger.exception(" Lỗi khi gọi Gemini API: {}", e)
            return "Tôi xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại sau."
            

    def classify_query(self, query: str) -> str:
        normalized = query.lower()
        greetings = ["chào", "xin chào", "hello", "helo", "hi", "yo", "bạn khỏe không"]
        personal = ["bạn là ai", "giới thiệu", "tên bạn", "chức năng", "làm gì", "giúp gì"]
        legal_keywords = ["điều", "luật", "quy định", "thuế", "pháp luật", "trách nhiệm", "nghĩa vụ"]

        def contains_exact(phrase_list):
            return any(re.search(rf"\b{re.escape(word)}\b", normalized) for word in phrase_list)

        if contains_exact(greetings) or contains_exact(personal):
            category = "greeting"
        elif contains_exact(legal_keywords):
            category = "legal"
        else:
            category = "general"

        logger.info("Phân loại câu hỏi: '{}' → {}", query, category)
        return category

    def build_prompt(self, query: str, search_results: list) -> str:
        category = self.classify_query(query)

        if category == "greetings":
            return f"""
Bạn là một trợ lý pháp lý thân thiện.

Người dùng hỏi:
\"{query}\"

 Hãy chào hỏi và giới thiệu bản thân ngắn gọn.  
 Không trả lời bất kỳ nội dung nào khác ngoài việc chào hỏi và giới thiệu.
""".strip()

        elif category == "legal" and search_results:
            context = "\n\n".join(f"{chunk['content']}" for chunk in search_results)
            return f"""
Bạn là một trợ lý pháp luật thông minh, nghiêm túc và trung thực.

Bạn **chỉ được phép trả lời các câu hỏi liên quan đến pháp luật Việt Nam và chỉ sử dụng nội dung trong tài liệu dưới đây**.

---
 Câu hỏi:
\"{query}\"

---
 Tài liệu:
{context}

---
 Trả lời đúng nội dung luật, rõ ràng, dễ hiểu.  
 Không suy đoán. Không sáng tạo. Không trả lời nếu thông tin không có trong tài liệu.

 Nếu không có đủ thông tin, hãy trả lời:  
"Tôi xin lỗi, tôi không có đủ thông tin trong tài liệu hiện tại để trả lời câu hỏi này."
""".strip()

        elif category == "legal" and not search_results:
            return f"""
Bạn là một trợ lý pháp luật nghiêm túc.

Câu hỏi:
\"{query}\"

Hiện tại, không có tài liệu nào liên quan đến câu hỏi này.

 Vui lòng trả lời:  
"Tôi xin lỗi, tôi không có đủ thông tin trong tài liệu hiện tại để trả lời câu hỏi này."
""".strip()

        else:
            return f"""
Bạn là một trợ lý pháp lý nghiêm túc.

Người dùng hỏi:
\"{query}\"

 Câu hỏi này không liên quan đến pháp luật.  
 Vui lòng trả lời:  
"Tôi xin lỗi, tôi chỉ hỗ trợ trả lời các câu hỏi liên quan đến pháp luật có trong tài liệu được cung cấp."
""".strip()

    def build_strict_prompt(self, query: str, chunk: dict) -> str:
        title = chunk.get("title", "")
        content = chunk.get("content", "")

        return f"""
Bạn là một trợ lý pháp lý chuyên nghiệp, nghiêm túc và chính xác.

Bạn chỉ được phép trả lời câu hỏi dựa trên nội dung dưới đây.

---
 Câu hỏi:
\"{query}\"

📘 Nội dung điều luật:
{title}
{content}

---
 Trả lời ngắn gọn, chính xác, **chỉ dựa vào nội dung trên**.  
 Không sáng tạo, không suy đoán.

 Nếu thông tin không nằm trong đoạn này, hãy trả lời:  
"Tôi không có đủ thông tin trong điều luật này để trả lời chính xác."
""".strip()
