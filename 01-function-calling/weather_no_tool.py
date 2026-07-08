"""Minh hoạ KHÔNG có function calling — model tự bịa câu trả lời."""

import os

from dotenv import load_dotenv
from openai import OpenAI

from prompts import SYSTEM_INSTRUCTION

load_dotenv()

client = OpenAI(
    base_url=os.getenv("NVIDIA_BASE_URL"),
    api_key=os.getenv("NVIDIA_API_KEY"),
)

MODEL = os.getenv("GLM_MODEL", "z-ai/glm-5.2")


def run(prompt: str) -> str:
    """Gửi *prompt* tới GLM-5.2 — không có tool nào để gọi, model tự trả lời."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"User: {question}\n")
    print("Trả lời (không có tool):", run(question))
