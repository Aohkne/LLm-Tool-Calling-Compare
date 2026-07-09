"""CLI thuần — công bố 2 tool `weather` và `exchange-rate` qua command-line,
KHÔNG qua MCP.

Khác với 02-mcp-basics: không có list_tools()/call_tool() tự động. Muốn biết
CLI này nhận subcommand/tham số gì, phải tự đọc --help (text tự do) hoặc đọc
source code. Không có schema, không có type-checking — kết quả trả về cũng
chỉ là text in ra stdout, ai gọi cũng phải tự parse.

Chạy trực tiếp:
    python weather_cli.py weather Hanoi
    python weather_cli.py exchange-rate USD
    python weather_cli.py --help
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared import mock_data  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="weather_cli.py",
        description="Tra cứu thời tiết hoặc tỷ giá ngoại tệ (mock).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    weather_parser = subparsers.add_parser("weather", help="Lấy thời tiết hiện tại của một thành phố")
    weather_parser.add_argument("city", help="Tên thành phố, ví dụ: Hanoi")

    rate_parser = subparsers.add_parser("exchange-rate", help="Lấy tỷ giá quy đổi sang VND")
    rate_parser.add_argument("currency", help="Mã ngoại tệ, ví dụ: USD")

    args = parser.parse_args()

    if args.command == "weather":
        print(mock_data.get_weather(args.city))
    elif args.command == "exchange-rate":
        print(mock_data.get_exchange_rate(args.currency))


if __name__ == "__main__":
    main()
