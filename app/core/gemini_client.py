import os
import openai
from dotenv import load_dotenv
import google.generativeai as genai
from app.utils.logger import logger  

load_dotenv()

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        api_key_openai = os.getenv("OPENAI_API_KEY")  # Lấy API key từ biến môi trường
        if not api_key:
            logger.error(" Không tìm thấy GEMINI_API_KEY trong file .env")
            raise ValueError("Missing GEMINI_API_KEY in .env")
        if not api_key_openai:
            logger.error(" Không tìm thấy OPENAI_API_KEY trong file .env")
            raise ValueError("Missing OPENAI_API_KEY in .env")
        
        self.GPT_client = openai.OpenAI(api_key=api_key_openai)
        genai.configure(api_key=api_key)
        logger.info("Đã khởi tạo GeminiClient")

    def chat(self, prompt: str, model_llm: str = "gemini-2.0-flash") -> str:
        try:
            if model_llm.startswith("gemini"):
                model = genai.GenerativeModel(model_llm)
                response = model.generate_content(prompt)
                logger.debug("Đã nhận phản hồi từ Gemini")
                return response.text

            elif model_llm.startswith("gpt"):
                response = self.GPT_client.chat.completions.create(
                            model=model_llm,  # Sử dụng model GPT-3.5 Turbo
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7
                        )
                logger.debug("Đã nhận phản hồi từ OpenAI GPT")
                return response.choices[0].message.content.strip()

            else:
                raise ValueError(f"Model '{model_llm}' không được hỗ trợ")

        except Exception as e:
            logger.exception("Lỗi khi gọi API: %s", e)
            return "Tôi xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại sau."

            

    def build_prompt(self, query: str, search_results: list, custom_instructions: str = None) -> str:
        """
        Tạo prompt dựa trên query và search_results.
        """
        context = "\n\n".join(chunk["content"] for chunk in search_results) if search_results else ""

        instructions = custom_instructions.strip() if custom_instructions else """
Bạn là một trợ lý pháp lý thân thiện, lịch sự và trung thực của Việt Nam.

Nhiệm vụ của bạn:
1. Nếu người dùng CHÀO HỎI → hãy trả lời chào hỏi tự nhiên, thân thiện.
2. Nếu người dùng hỏi VỀ PHÁP LUẬT → bạn chỉ được phép trả lời dựa trên TÀI LIỆU dưới đây (nếu có) và giải thích rõ ràng nếu người dùng cần,không hiểu.
3. Nếu câu hỏi KHÔNG LIÊN QUAN đến pháp luật → hãy lịch sự từ chối và nói rằng bạn chỉ hỗ trợ câu hỏi pháp luật.
4. Nếu không tìm thấy nội dung liên quan trong tài liệu → hãy trả lời: 
"Tôi xin lỗi, tôi không có đủ thông tin trong tài liệu hiện tại để trả lời câu hỏi này."
        """.strip()

        prompt = f"""
{instructions}

---
Câu hỏi của người dùng:
"{query}"

---
Tài liệu (nếu có):
{context}

---
Hãy đưa ra câu trả lời phù hợp nhất theo đúng quy tắc trên.
        """.strip()

        return prompt
