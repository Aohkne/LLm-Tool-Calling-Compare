"""Agent + LLM — model quyết định gọi tool qua FUNCTION CALLING, agent thực
thi bằng cách gọi CLI (weather_cli.py) qua subprocess — KHÔNG qua MCP.

Điểm mấu chốt để so sánh với 02-mcp-basics (weather_client.py):
  - Không có list_tools(): schema dưới đây phải viết TAY (giống 01), agent
    phải tự biết trước weather_cli.py nhận subcommand/tham số gì.
  - Model vẫn "chọn hàm" y hệt Function Calling thuần — sự khác biệt duy nhất
    nằm ở BÊN TRONG hàm: thay vì tính trực tiếp, nó spawn subprocess gọi CLI.
  - Nếu weather_cli.py đổi cú pháp, phải tự sửa lại đúng chỗ subprocess này —
    không có cơ chế phát hiện tự động như MCP.

Cách chạy (cùng thư mục với weather_cli.py):
    pip install -r ../requirements.txt
    cp ../.env.example ../.env
    python weather_agent_cli.py
"""

import json
import os
import subprocess
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # tự tìm .env ở thư mục gốc repo (dùng chung cho 01/02/03)

client = OpenAI(
    base_url=os.getenv("NVIDIA_BASE_URL"),
    api_key=os.getenv("NVIDIA_API_KEY"),
)
MODEL = os.getenv("GLM_MODEL")

# 1. Schema viết tay — CLI không tự công bố được như MCP list_tools()
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Lấy thời tiết hiện tại của một thành phố",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "Tên thành phố"}},
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
                "properties": {"currency": {"type": "string", "description": "Mã ngoại tệ, ví dụ: USD"}},
                "required": ["currency"],
            },
        },
    },
]


# 2. Agent thực thi bằng cách gọi CLI qua subprocess — hard-code cú pháp CLI
def get_weather(city: str) -> str:
    result = subprocess.run(
        [sys.executable, "weather_cli.py", "weather", city],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def get_exchange_rate(currency: str) -> str:
    result = subprocess.run(
        [sys.executable, "weather_cli.py", "exchange-rate", currency],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


TOOL_IMPLS = {"get_weather": get_weather, "get_exchange_rate": get_exchange_rate}


def run(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]

    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    message = resp.choices[0].message

    while message.tool_calls:
        messages.append(message)

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            fn = TOOL_IMPLS[tool_call.function.name]
            print(f"  [model yêu cầu] {tool_call.function.name}({args})")
            result = fn(**args)  # <-- subprocess gọi weather_cli.py
            print(f"  [subprocess]    -> {result}")
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        message = resp.choices[0].message

    return message.content


if __name__ == "__main__":
    question = "Thời tiết Cần Thơ hôm nay thế nào? Và tỷ giá USD hôm nay bao nhiêu?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
