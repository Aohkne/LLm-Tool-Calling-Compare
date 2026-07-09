# 01 — Function Calling thuần (GLM-5.2 qua NVIDIA API, OpenAI-compatible)

Tool `get_weather` + `get_exchange_rate` được **định nghĩa schema thủ công** và
**thực thi ngay trong app**. Model chỉ quyết định gọi tool nào — app mới là nơi chạy.

```mermaid
flowchart TD
    A["User hỏi"] --> B["Model quyết định gọi<br/>get_weather(city='Cần Thơ')"]
    B --> C["App TỰ THỰC THI hàm get_weather"]
    C --> D["Model tổng hợp câu trả lời"]
```

## Cách chạy

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # điền NVIDIA_API_KEY ở gốc repo (dùng chung với 02/03)

python weather_function_calling.py   # có tool
python weather_no_tool.py            # không có tool — để so sánh
```

## File

| File | Mô tả |
|---|---|
| `weather_function_calling.py` | Định nghĩa schema, thực thi tool, gọi GLM-5.2, xử lý vòng lặp function calling |
| `weather_no_tool.py` | Cùng câu hỏi nhưng KHÔNG truyền tool nào — model tự bịa/từ chối trả lời |
| `prompts.py` | System prompt dùng chung cho cả 2 file trên |

---

## Function Calling là gì? Giải thích đơn giản

Hình dung bạn có một **trợ lý ảo** rất giỏi ngôn ngữ, nhưng **không biết gì về thế giới thật** — không biết thời tiết, không truy cập được database, không gọi được API.

Function Calling là cách bạn **dạy trợ lý ảo sử dụng công cụ**:

```mermaid
flowchart LR
    subgraph NoFC["Không có Function Calling"]
        direction TB
        A1["User: 'Thời tiết HN?'"] --> A2["Model"]
        A2 --> A3["'Tôi không biết'<br/>(bó tay vì không có dữ liệu)"]
    end

    subgraph FC["Có Function Calling"]
        direction TB
        B1["User: 'Thời tiết HN?'"] --> B2["Model<br/>(biết có tool get_weather)"]
        B2 --> B3["'Hãy gọi get_weather(city=HN)'"]
        B3 --> B4["App chạy hàm"]
        B4 --> B5["Model: 'HN: 29°C, mưa'"]
    end

    NoFC ~~~ FC
```

**Điểm mấu chốt:** Model **KHÔNG chạy** hàm. Nó chỉ nói *"hãy gọi hàm X với tham số Y"*.

---

## Minh hoạ từng bước chi tiết

User hỏi: **"Thời tiết Cần Thơ hôm nay thế nào? Và tỷ giá USD hôm nay bao nhiêu?"**

```mermaid
sequenceDiagram
    participant App
    participant M as GLM-5.2

    Note over App: Bước 1 — Chuẩn bị schema tool THỦ CÔNG<br/>get_weather(city), get_exchange_rate(currency)<br/>mỗi tool ~15 dòng code, phải khớp với hàm thật

    App->>M: Bước 2 — Gửi prompt + schema<br/>"Thời tiết Cần Thơ? Tỷ giá USD?"
    Note over M: Hiểu: cần gọi 2 tool khác nhau

    M-->>App: Bước 3 — tool_calls (không tự chạy!)<br/>get_weather(city="Cần Thơ")<br/>get_exchange_rate(currency="USD")
    Note over M: Model CHỈ sinh JSON — không hề chạy

    Note over App: Bước 4 — Tự thi hành hàm Python<br/>get_weather("Cần Thơ") → "31°C, nắng nóng"<br/>get_exchange_rate("USD") → "1 USD = 25,400 VND"

    App->>M: Bước 5 — Gửi kết quả (role="tool")
    M-->>App: "Cần Thơ 31°C nắng nóng 🌤️, tỷ giá USD hôm nay 25.400 VND"
```

---

## Nhìn vào code thật

3 phần quan trọng trong `weather_function_calling.py`:

**Phần 1 — Schema viết tay** (model cần biết tool trông như thế nào — định dạng JSON Schema chuẩn OpenAI-compatible):

```python
# App phải TỰ MÔ TẢ tool cho model — viết tay, dễ sai
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
    # ... get_exchange_rate tương tự
]
```

**Phần 2 — Hàm thực thi** (app tự chạy khi model yêu cầu, dùng chung `shared/mock_data.py`):

```python
# App phải CÓ hàm thật để chạy — model không chạy hàm này
from shared.mock_data import get_weather, get_exchange_rate
TOOL_IMPLS = {"get_weather": get_weather, "get_exchange_rate": get_exchange_rate}
```

**Phần 3 — Vòng lặp** (nhận yêu cầu → chạy → trả lại):

```python
while message.tool_calls:
    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        fn = TOOL_IMPLS[tool_call.function.name]
        result = fn(**args)   # ← APP chạy, không phải model
    # gửi result lại cho model (role="tool") để tổng hợp câu trả lời
```

---

## Luồng hoạt động

1. App định nghĩa tool bằng JSON Schema viết tay (tên, tham số, kiểu)
2. App gửi prompt + danh sách tool tới GLM-5.2 (qua NVIDIA API)
3. Model trả về `tool_calls` — yêu cầu gọi tool phù hợp
4. App **tự chạy** hàm tương ứng và đưa kết quả trả lại model (role `"tool"`)
5. Model tổng hợp câu trả lời cuối cho user

---

Bước tiếp theo: [`../README.md`](../README.md) — so sánh Function Calling với MCP (02) và CLI (03).
