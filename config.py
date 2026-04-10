DEEPSEEK_API_KEY = "sk-2816057f8396437484bfeb98cd558f03"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# AI-2：3D 场景质量评估员（可单独配置 key，默认复用 AI-1 的 key）
DEEPSEEK_API_KEY_2 = "sk-2816057f8396437484bfeb98cd558f03"  # 可替换为独立 key
DEEPSEEK_EVALUATOR_TEMP = 0.5   # 比 AI-1(0.3) 稍高，评语更灵活

# Blender configuration
BLENDER_EXECUTABLE = "F:/Blender/blender.exe"
BLENDER_TIMEOUT = 120  # seconds per scene

# Scene feature toggles
ENABLE_ROADS = False  # Set to True to re-enable road mesh generation and overlap checks