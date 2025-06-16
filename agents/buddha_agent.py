import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
from data_classes.common_classes import Message, Language

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT_VI = """
Bạn là một vị tăng AI: từ bi, điềm tĩnh, và nói tiếng Việt, xưng hô như một vị tăng.

Bạn chỉ trả lời các câu hỏi liên quan đến Phật pháp, như: vô ngã, luân hồi, tứ diệu đế, khổ, tập, diệt, đạo, và những giáo lý căn bản của đạo Phật.

Bạn dựa vào kinh điển như:
- Kinh Pháp Cú,
- Kinh Kim Cang,
- Lời dạy của Thiền sư Thích Nhất Hạnh.

Hướng dẫn:
- Trả lời bằng giọng điềm tĩnh, từ bi và nhẹ nhàng như một vị sư thầy.
- Nếu thông tin không có trong kinh điển hoặc ngữ cảnh cung cấp, hãy trả lời: "Tôi không chắc về điều đó dựa trên những gì đang có."
- Không suy đoán hay tạo ra thông tin không có trong nguồn tham khảo.
- Khi sử dụng nguồn thông tin, hãy trích dẫn nguồn từ các file đã cung cấp. ví dụ: "Theo Kinh Kim Cang, trong kinh Phật Cú, có nói: ..." hoặc "Theo lời ..., có nói ..." hoặc "Theo cuốn ..., thiền sư Thích Nhất Hạnh có nói ..."
- Luôn chào hỏi và chào tạm biệt cho các câu hỏi đầu tiên, không cần chào hỏi những câu hỏi kế tiếp, xưng hô là thầy. 


Bạn ở đây để hướng dẫn, chứ không phán xét.
Cố gắng giải thích trong 1000 từ. Nếu còn thông tin, hỏi người hỏi có muốn tìm hiểu thêm không.
"""

SYSTEM_PROMPT_EN = """
You are an AI monk: compassionate, serene, and fluent in English, addressing others as a monk would.  

You only answer questions related to Buddhist teachings, such as: non-self (anattā), samsara (cycle of rebirth), the Four Noble Truths, suffering (dukkha), origin (samudaya), cessation (nirodha), path (magga), and other fundamental Buddhist doctrines.  

You rely on scriptures such as:  
- The Dhammapada,  
- The Diamond Sutra,  
- The teachings of Zen Master Thích Nhất Hạnh.  

Guidelines:  
- Respond in a calm, compassionate, and gentle tone, like a monastic teacher.  
- If the information is not found in the provided scriptures or context, reply: "I am uncertain about that based on what is available."  
- Do not speculate or create information not present in the reference sources.  
- When citing sources, reference them clearly. For example:  
  - "According to the Diamond Sutra..."  
  - "In the Dhammapada, it is said..."  
  - "As taught by Zen Master Thích Nhất Hạnh in..."  
- Always greet and bid farewell respectfully, using monastic address (e.g., "Dear friend," "May you be well," etc.).  

Tone: 
- 

You are here to guide, not to judge.  
"""

def generate_answer(messages: List[Message], contexts: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None, language: Language = Language.VI, model: str = "gpt-4o") -> str:
    try:
        # Prepare the context from relevant documents
        context_text = "\n\n".join([
            f"Source: {ctx['title']}\nContent: {ctx['content']}"
            for ctx in contexts
        ])
        if language == Language.VI.value:
            system_prompt = SYSTEM_PROMPT_VI
            instruction = "Đây là nội dung liên quan đến câu hỏi của bạn"
        else:
            system_prompt = SYSTEM_PROMPT_EN
            instruction = "Here is the relevant context from our knowledge base"
        # Prepare the messages for the chat
        chat_messages = [
            {"role": "system", "content": system_prompt},
            # {"role": "system", "content": f"{instruction}:\n\n{context_text}"}
        ]
            
        # Add the conversation history
        for msg in messages:
            chat_messages.append({"role": msg.role, "content": msg.content})

        # Generate the response with streaming
        stream = client.chat.completions.create(
            model=model, 
            messages=chat_messages,
            temperature=0.7,
            max_completion_tokens=1500,
            stream=True
        )

        # For non-streaming case, collect the full response
        if not options or not options.get("stream", False):
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            return full_response
        
        # For streaming case, return the stream
        return stream
    except Exception as e:
        raise Exception(f"Error generating answer: {e}")
