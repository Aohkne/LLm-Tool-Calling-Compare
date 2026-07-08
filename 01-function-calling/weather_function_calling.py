"""Minh hoạ FUNCTION CALLING thuần"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from prompts import SYSTEM_INSTRUCTION

load_dotenv()

client = OpenAI(
    base_url=os.getenv("NVIDIA_BASE_URL"),
    api_key=os.getenv("NVIDIA_API_KEY"),
)

MODEL = os.getenv("GLM_MODEL")

# 1. App tự định nghĩa schema của tool (định dạng OpenAI function calling)
GET_WEATHER_TOOL = {
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
}


# 2. App tự thực thi tool (trong thực tế sẽ gọi API thời tiết thật)
def get_weather(city: str) -> str:
    """Trả về thời tiết (mock) của *city*. Dùng làm tool cho model."""
    mock_data = {
        "Hà Nội": {
            "nhiệt_độ": "29°C",
            "thời_tiết": "trời mưa nhẹ",
            "độ_ẩm": "82%",
            "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
        },
        "Hồ Chí Minh": {
            "nhiệt_độ": "33°C",
            "thời_tiết": "mưa rào",
            "độ_ẩm": "75%",
            "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
        },
        "Đà Nẵng": {
            "nhiệt_độ": "30°C",
            "thời_tiết": "nhiều mây",
            "độ_ẩm": "78%",
            "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
        },
    }
    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps({"city": city, **mock_data.get(city, default)}, ensure_ascii=False)


def run(prompt: str) -> str:
    """Gửi *prompt* tới GLM-5.2, tự động xử lý function calling và trả về câu trả lời cuối."""
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]

    # 3. Gọi model — model quyết định có gọi tool hay không
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[GET_WEATHER_TOOL],
    )
    message = resp.choices[0].message

    # 4. Vòng lặp: nếu model yêu cầu tool, app TỰ THỰC THI rồi đưa kết quả trả lại
    while message.tool_calls:
        # Thêm phản hồi của model vào lịch sử hội thoại
        messages.append(message)

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            print(f"  [model yêu cầu] {tool_call.function.name}({args})")
            result = get_weather(**args)  # <-- app chạy, không phải model
            print(f"  [app thực thi]  -> {result}")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[GET_WEATHER_TOOL],
        )
        message = resp.choices[0].message

    # 5. Model tổng hợp câu trả lời cuối
    return message.content


if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
