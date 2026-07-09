"""MCP CLIENT + LLM — kết nối weather_server.py qua giao thức MCP, dùng GLM
(qua Function Calling) để THẬT SỰ quyết định gọi tool nào.

Khác với bản demo thuần giao thức: ở đây schema tool được lấy tự động qua
list_tools() rồi đưa cho model dưới dạng Function Calling — không ai viết tay
JSON schema như 01-function-calling. Model chọn tool, MCP client gọi
call_tool() để SERVER thực thi và trả kết quả về.

Cách chạy (cùng thư mục với weather_server.py, client tự khởi động server):
    pip install -r ../requirements.txt
    cp ../.env.example ../.env   # điền NVIDIA_API_KEY (dùng chung với 01/03)
    cd 02-mcp-basics
    python weather_client.py
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool
from openai import OpenAI

load_dotenv()

llm = OpenAI(
    base_url=os.getenv("NVIDIA_BASE_URL"),
    api_key=os.getenv("NVIDIA_API_KEY"),
)
MODEL = os.getenv("GLM_MODEL")


def _to_openai_tool(tool: Tool) -> dict:
    """Chuyển schema MCP (tự sinh qua list_tools) sang định dạng Function Calling."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


async def ask(session: ClientSession, tools: list[dict], question: str) -> str:
    messages = [{"role": "user", "content": question}]

    # Model quyết định có gọi tool hay không, và gọi tool nào trong `tools`
    resp = llm.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    message = resp.choices[0].message

    while message.tool_calls:
        messages.append(message)

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            print(f"  [model yêu cầu] {tool_call.function.name}({args})")

            # MCP SERVER thực thi tool — client không biết/không cần biết code bên trong
            result = await session.call_tool(tool_call.function.name, args)
            text = result.content[0].text
            print(f"  [MCP server]   -> {text}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": text,
            })

        resp = llm.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        message = resp.choices[0].message

    return message.content


async def main() -> None:
    # Dùng đúng interpreter đang chạy client (tránh lỗi "python" không tồn tại)
    params = StdioServerParameters(command=sys.executable, args=["weather_server.py"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. KHÁM PHÁ tool + schema tại runtime (không hard-code như 01)
            tools_result = await session.list_tools()
            tools = [_to_openai_tool(t) for t in tools_result.tools]
            print("Tools MCP server cung cấp:")
            for t in tools_result.tools:
                print(f"  - {t.name}: {t.description}")

            # 2. Model quyết định gọi tool nào (Function Calling), MCP server thực thi
            question = "Thời tiết Cần Thơ hôm nay thế nào? Và tỷ giá USD hôm nay bao nhiêu?"
            print(f"\nUser: {question}\n")
            answer = await ask(session, tools, question)
            print("\nTrả lời:", answer)


if __name__ == "__main__":
    asyncio.run(main())
