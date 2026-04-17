"""
Step 1: 调用 DeepSeek API，将文本提示词转为场景 JSON

根据提示词中的布局风格关键词，自动加载对应 skill 的 system_prompt.txt，
未识别到风格时使用通用兜底 prompt。
"""

import requests
import json
from pathlib import Path
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL

# ---------------------------------------------------------------------------
# Skill 目录
# ---------------------------------------------------------------------------

SKILLS_DIR = Path(__file__).parent / "skills"

# 风格关键词映射（先匹配先生效，顺序有意义）
STYLE_KEYWORDS: dict[str, list[str]] = {
    "orthogonal_grid": ["方格网布局", "正交网格", "orthogonal grid", "方格网式"],
    "slab_row":        ["行列式", "板式行列", "slab row"],
    "point_scatter":   ["点式散布", "point scatter", "塔楼散点"],
    "perimeter":       ["周边式围合", "周边式", "围合布局", "courtyard", "perimeter"],
    "radial":          ["放射式", "辐射型", "radial"],
    "cluster":         ["组团式", "组团布局", "cluster"],
    "organic":         ["有机自由式", "有机式", "自由式布局", "organic", "irregular"],
}


def detect_style(text: str) -> str | None:
    """扫描提示词中的布局风格关键词，返回对应 skill 目录名；未匹配返回 None。"""
    for style, keywords in STYLE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return style
    return None


def load_skill_prompt(style: str | None) -> str:
    """加载指定风格的 system_prompt.txt；style=None 时加载通用兜底 prompt。"""
    if style:
        path = SKILLS_DIR / style / "assets" / "system_prompt.txt"
    else:
        path = SKILLS_DIR / "_common" / "assets" / "base_system_prompt.txt"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 主调用函数
# ---------------------------------------------------------------------------

def text_to_scene_json(text: str) -> dict:
    """调用 DeepSeek API，将文本提示词转为场景 JSON"""
    style = detect_style(text)
    system_prompt = load_skill_prompt(style)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
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

    # 清理：去除可能的 markdown 代码块包裹
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
        # 截断修复：找到最后一个完整的 } 尝试补全
        print(f"[step1] WARNING: JSON parse error ({e}), attempting repair…")
        # 找到最后一个完整闭合位置
        for end in range(len(content), 0, -1):
            try:
                return json.loads(content[:end])
            except json.JSONDecodeError:
                continue
        raise RuntimeError(
            f"DeepSeek 返回的内容无法解析为 JSON（token 可能仍然不足）。\n"
            f"原始错误：{e}\n"
            f"内容末尾 200 字符：…{content[-200:]}"
        )
