"""将 run_backend.py 复制到 backend/ 目录"""

import shutil
from pathlib import Path

src = Path(__file__).parent / "run_backend.py"
dst = Path("backend/run_backend.py")

shutil.copy2(src, dst)
print(f"Copied {src} -> {dst}")
