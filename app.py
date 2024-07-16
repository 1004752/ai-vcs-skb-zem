import os
import streamlit as st
from openai import OpenAI
import base64
from dotenv import load_dotenv
import sqlite3
from datetime import datetime


# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('qa_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS qa_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT,
                  answer TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    return conn


# 질문과 답변 저장
def save_qa(conn, question, answer):
    c = conn.cursor()
    c.execute("INSERT INTO qa_history (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()


# 히스토리 불러오기
def load_history(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM qa_history ORDER BY timestamp DESC")
    return c.fetchall()


# Streamlit 앱 설정
st.set_page_config(layout="wide")

# 데이터베이스 연결
conn = init_db()

load_dotenv()

# 메인 레이아웃
col1, col2 = st.columns([2, 1])

with col1:
    st.title("📝 SKB ZEM Q&A with OpenAI")

    # with st.sidebar:
    #     openai_api_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY"), key="file_qa_api_key", type="password")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    uploaded_files = st.file_uploader("Upload articles or images", type=["css", "scss", "vue", "png", "jpg", "jpeg"], accept_multiple_files=True)
    question = st.text_area(
        "Ask something about the uploaded files",
        placeholder="Can you describe these images?" if any(file.type.startswith('image') for file in uploaded_files) else "Can you give me a short summary of these files?",
        height=100,
        disabled=not uploaded_files,
    )

    submit_button = st.button("Get AI Response", disabled=not (uploaded_files and question and openai_api_key))

    if submit_button:
        client = OpenAI(api_key=openai_api_key)

        st.write("### Answer")
        answer_container = st.empty()
        full_response = ""

        messages = [{"role": "system", "content": "You are a helpful assistant that answers questions about multiple files."}]

        for file in uploaded_files:
            if file.type.startswith('image'):
                image_data = file.getvalue()
                base64_image = base64.b64encode(image_data).decode('utf-8')
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{file.type};base64,{base64_image}"}}
                    ]
                })
            else:
                content = file.read().decode()
                messages.append({"role": "user", "content": f"File {file.name}:\n\n{content}"})

        messages.append({"role": "user", "content": f"Question: {question}"})

        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4096,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                answer_container.markdown(full_response + "▌")

        answer_container.markdown(full_response)

        # 질문과 답변 저장
        save_qa(conn, question, full_response)

    for file in uploaded_files:
        if file.type.startswith('image'):
            st.image(file, caption=f'Uploaded Image: {file.name}', use_column_width=True)

with col2:
    st.title("Question History")
    history = load_history(conn)
    for item in history:
        with st.expander(f"Q: {item[1][:50]}..."):
            st.write(f"Question: {item[1]}")
            st.write(f"Answer: {item[2]}")
            st.write(f"Time: {item[3]}")

# 데이터베이스 연결 종료
conn.close()
