"""MCP SERVER minh hoạ — công bố tool `get_weather` qua giao thức MCP.

Khác với function calling: tool nằm ở một server ĐỘC LẬP. Server tự "khai
báo" tool của mình; bất kỳ MCP client nào (Claude Code, Claude Desktop,
Cursor, hoặc weather_client.py) cũng cắm vào dùng được mà không cần biết
code bên trong.

Schema của tool được TỰ ĐỘNG sinh ra từ type hints + docstring.

Chạy trực tiếp:
    pip install -r ../requirements.txt
    python weather_server.py

Đăng ký với Claude Code (làm 1 lần, dùng mãi):
    cd /đường dẫn hiện tại
    pwd -> copy
    claude mcp add weather -- python /đường/dẫn/tới/weather_server.py
"""

import os
import sys

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared import mock_data  # noqa: E402

mcp = FastMCP("weather")

_NAME = "LÊ HỮU KHOA"


@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    return mock_data.get_weather(city)


@mcp.tool()
def get_exchange_rate(currency: str) -> str:
    """Lấy tỷ giá quy đổi sang VND của một loại ngoại tệ hôm nay."""
    return mock_data.get_exchange_rate(currency)


@mcp.tool()
def get_name() -> str:
    """Lấy tên của tool"""
    return f"{_NAME}"


if __name__ == "__main__":
    mcp.run()  # mặc định chạy qua stdio
