"""
Step 1: 调用 DeepSeek API，将文本提示词转为场景 JSON（顶点坐标格式）
"""

import requests
import json
from pathlib import Path
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL

_SYSTEM_PROMPT = (
    Path(__file__).parent / "skills" / "_common" / "assets" / "base_system_prompt.txt"
).read_text(encoding="utf-8")


def text_to_scene_json(text: str) -> dict:
    """调用 DeepSeek API，将文本提示词转为场景 JSON（顶点坐标格式）"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=180)
    if not resp.ok:
        print(f"[step1] API error {resp.status_code}: {resp.text[:500]}")
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]

    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[step1] WARNING: JSON parse error ({e}), attempting repair…")
        for end in range(len(content), 0, -1):
            try:
                return json.loads(content[:end])
            except json.JSONDecodeError:
                continue
        raise RuntimeError(
            f"DeepSeek 返回的内容无法解析为 JSON。\n"
            f"原始错误：{e}\n"
            f"内容末尾 200 字符：…{content[-200:]}"
        )
