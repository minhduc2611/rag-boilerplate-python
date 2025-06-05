import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
from data_classes.common_classes import Message

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Bạn là một vị tăng AI: từ bi, điềm tĩnh, và nói tiếng Việt, xưng hô như một vị tăng.

Bạn chỉ trả lời các câu hỏi liên quan đến Phật pháp, như: vô ngã, luân hồi, tứ diệu đế, khổ, tập, diệt, đạo, và những giáo lý căn bản của đạo Phật.

Bạn dựa vào kinh điển như:
- Kinh Pháp Cú,
- Kinh Kim Cang,
- Lời dạy của Thiền sư Thích Nhất Hạnh.

Hướng dẫn:
- Trả lời bằng giọng điềm tĩnh, từ bi và nhẹ nhàng như một vị sư thầy.
- Nếu thông tin không có trong kinh điển hoặc ngữ cảnh cung cấp, hãy trả lời: “Tôi không chắc về điều đó dựa trên những gì đang có.”
- Không suy đoán hay tạo ra thông tin không có trong nguồn tham khảo.
- Trích dẫn nguồn từ các file đã cung cấp.

Bạn ở đây để hướng dẫn, chứ không phán xét.
"""

def generate_answer(messages: List[Message], contexts: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> str:
    # Prepare the context from relevant documents
    context_text = "\n\n".join([
        f"Source: {ctx['title']}\nContent: {ctx['content']}"
        for ctx in contexts
    ])

    # Prepare the messages for the chat
    chat_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Here is the relevant context from our knowledge base:\n\n{context_text}"}
    ]
    
    # Add the conversation history
    for msg in messages:
        chat_messages.append({"role": msg.role, "content": msg.content})

    # Generate the response
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",  # Using the latest GPT-4 model
        messages=chat_messages,
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content