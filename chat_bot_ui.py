import os
import requests
import streamlit as st


st.set_page_config(page_title="ChatBot Luật Việt Nam", layout="wide")
st.title("📘 ChatBot Luật Việt Nam")

with st.sidebar:
    st.header("⚙️ Cấu hình tìm kiếm")
    mode = st.radio("Phương pháp tìm kiếm", ["hybrid", "vector", "keyword"])
    top_k = st.slider("Số kết quả (top_k)", 1, 100, 5)
    alpha = st.slider("Độ cân bằng (alpha)", 0.0, 1.0, 0.6) if mode == "hybrid" else None

    st.markdown("---")
    st.header("📤 Tải tài liệu luật")
    uploaded_file = st.file_uploader("Chọn file DOCX", type=["docx"])

    if uploaded_file:
        if st.button("🚀 Upload và xử lý"):
            with st.spinner("Đang tải và xử lý tài liệu..."):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    }
                    response = requests.post("http://localhost:8000/upload", files=files)
                    res = response.json()

                    if response.status_code == 200:
                        st.success(f"✅ Tải lên thành công: {res['filename']}")
                        st.info(f"Đã tạo doc_id: {res['doc_id']} với {res['total_chunks']} đoạn.")
                    else:
                        st.error(f"❌ Lỗi từ server: {res.get('detail', 'Không rõ nguyên nhân.')}")
                except Exception as e:
                    st.error(f"❌ Lỗi khi gửi file: {e}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("Nhập câu hỏi của bạn...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.spinner("🔍 Đang tìm kiếm và phản hồi..."):
        try:
            params = {"query": query, "mode": mode, "top_k": top_k}
            if alpha is not None:
                params["alpha"] = alpha

            response = requests.get("http://localhost:8000/chat", params=params)
            data = response.json()

            answer = data.get("answer", "Không có phản hồi.")
        except Exception as e:
            answer = f"❌ Lỗi khi gọi API: {e}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
