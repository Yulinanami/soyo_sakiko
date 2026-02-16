"""修正 Frozen 环境下的 .env 路径"""

import sys
from pathlib import Path

p = Path("backend/app/services/credential_service.py")
content = p.read_text(encoding="utf-8")

# 替换 _write_env 方法中的路径逻辑
old_line = 'env_path = Path(__file__).resolve().parents[2] / ".env"'
new_block = (
    "import sys; "
    'env_path = (Path(sys.executable).parent / ".env") '
    'if getattr(sys, "frozen", False) else '
    '(Path(__file__).resolve().parents[2] / ".env")'
)

if old_line in content:
    new_content = content.replace(old_line, new_block)
    p.write_text(new_content, encoding="utf-8")
    print("Successfully patched credential_service.py")
else:
    print("Warning: Could not find target line to patch in credential_service.py")
    sys.exit(1)
