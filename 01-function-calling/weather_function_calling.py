"""Minh hoạ FUNCTION CALLING thuần"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.mock_data import get_exchange_rate, get_weather  # noqa: E402

from prompts import SYSTEM_INSTRUCTION

load_dotenv()

client = OpenAI(
    base_url=os.getenv("NVIDIA_BASE_URL"),
    api_key=os.getenv("NVIDIA_API_KEY"),
)

MODEL = os.getenv("GLM_MODEL")

# 1. App tự định nghĩa schema của tool (định dạng OpenAI function calling)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy thời tiết hiện tại của một thành phố",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Tên thành phố"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Lấy tỷ giá quy đổi sang VND của một loại ngoại tệ hôm nay",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {"type": "string", "description": "Mã ngoại tệ, ví dụ: USD"},
                },
                "required": ["currency"],
            },
        },
    },
]

# 2. App tự thực thi tool
TOOL_IMPLS = {"get_weather": get_weather, "get_exchange_rate": get_exchange_rate}


def run(prompt: str) -> str:
    """Gửi *prompt* tới GLM-5.2, tự động xử lý function calling và trả về câu trả lời cuối."""
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]

    # 3. Gọi model — model quyết định gọi tool nào trong TOOLS (nếu cần)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )
    message = resp.choices[0].message

    # 4. Vòng lặp: nếu model yêu cầu tool, app TỰ THỰC THI rồi đưa kết quả trả lại
    while message.tool_calls:
        # Thêm phản hồi của model vào lịch sử hội thoại
        messages.append(message)

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            fn = TOOL_IMPLS[tool_call.function.name]
            print(f"  [model yêu cầu] {tool_call.function.name}({args})")
            result = fn(**args)  # <-- app chạy, không phải model
            print(f"  [app thực thi]  -> {result}")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = resp.choices[0].message

    # 5. Model tổng hợp câu trả lời cuối
    return message.content


if __name__ == "__main__":
    question = "Thời tiết Cần Thơ hôm nay thế nào? Và tỷ giá USD hôm nay bao nhiêu?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
