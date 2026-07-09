"""Mock data + hàm tra cứu dùng chung cho cả 3 cách: Function Calling (01),
MCP (02), CLI (03) — để đảm bảo cả 3 module minh hoạ CÙNG một bộ dữ liệu,
chỉ khác nhau ở cách công bố/gọi tool.
"""

import unicodedata

WEATHER_DB = {
    "Hanoi": "29°C, trời mưa",
    "Haiphong": "33°C, mưa rào",
    "Danang": "30°C, nhiều mây",
    "Can Tho": "31°C, nắng nóng",
}

EXCHANGE_RATE_DB = {
    "USD": 25_400,
    "EUR": 27_200,
    "JPY": 165,
}


def _normalize(text: str) -> str:
    """Bỏ dấu + hạ chữ thường, để "Cần Thơ" khớp với key "Can Tho".

    Model thường trả tên thành phố có dấu tiếng Việt dù mock DB lưu không dấu
    — cần chuẩn hoá cả hai phía trước khi so khớp.
    """
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower().strip()


_WEATHER_LOOKUP = {_normalize(city): weather for city, weather in WEATHER_DB.items()}


def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    weather = _WEATHER_LOOKUP.get(_normalize(city))
    if weather is None:
        return f"{city}: 28°C, không có dữ liệu chi tiết"
    return f"{city}: {weather}"


def get_exchange_rate(currency: str = "USD") -> str:
    """Lấy tỷ giá quy đổi sang VND của một loại ngoại tệ hôm nay."""
    rate = EXCHANGE_RATE_DB.get(currency.upper())
    if rate is None:
        return f"Không có dữ liệu tỷ giá cho {currency}"
    return f"1 {currency.upper()} = {rate:,} VND"
