"""Mizuoto TTS WebUI 配置"""

import logging
import os
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[1]
"""项目根目录"""

DATA_PATH = ROOT_PATH / "data"
"""Mizuoto 数据目录 (设置, 数据库, 模型, 输出和缓存)"""

REQUIREMENTS_PATH = ROOT_PATH / "requirements.txt"
"""依赖记录文件路径"""

LOGGER_NAME = os.getenv("MIZUOTO_TTS_WEBUI_LOGGER_NAME", "Mizuoto-TTS-WebUI")
"""日志器名称"""

LOGGER_LEVEL = int(os.getenv("MIZUOTO_TTS_WEBUI_LOGGER_LEVEL", str(logging.INFO)))
"""日志等级"""

LOGGER_COLOR = os.getenv("MIZUOTO_TTS_WEBUI_LOGGER_COLOR", "1").lower() not in {"0", "false", "none"}
"""是否启用彩色日志"""

DEFAULT_SERVER_HOST = "127.0.0.1"
"""默认监听地址"""

DEFAULT_SERVER_PORT = 7869
"""默认监听端口 (与 mizuoto 默认端口一致)"""

TORCH_MIN_VERSION = "2.8"
"""Mizuoto 需要的最低 PyTorch 版本"""

PYTORCH_INDEX_URL = "https://download.pytorch.org/whl"
"""PyTorch 官方软件包索引"""

PYTORCH_INSTALL_ARGS: dict[str, list[str]] = {
    "cuda": ["torch==2.14.0", "--index-url", f"{PYTORCH_INDEX_URL}/cu130"],
    "cuda128": [f"torch>={TORCH_MIN_VERSION}", "--index-url", f"{PYTORCH_INDEX_URL}/cu128"],
    "cuda126": [f"torch>={TORCH_MIN_VERSION}", "--index-url", f"{PYTORCH_INDEX_URL}/cu126"],
    "rocm": ["torch[device-all]==2.13.0+rocm10.0.0", "--index-url", "https://stable.repo.amd.com/rocm/whl-next"],
    "xpu": ["torch==2.14.0+xpu", "--index-url", f"{PYTORCH_INDEX_URL}/xpu"],
    "mps": ["torch==2.14.0"],
    "cpu": ["torch==2.14.0", "--index-url", f"{PYTORCH_INDEX_URL}/cpu"],
}
"""各 PyTorch 类型的 Pip 安装参数

cuda / xpu / mps / cpu 使用 PyTorch 官方软件包索引, 与 mizuoto 文档 (Install) 一致

- cuda128 / cuda126: 驱动不支持 CUDA 13.0 (驱动版本低于 580) 时的回退类型, 不固定 PyTorch 版本
- rocm: 使用 AMD 的软件包索引, 同时支持 Windows 和 Linux (mizuoto 文档中的 download.pytorch.org/whl/rocm7.2 仅支持 Linux)

未提供 DirectML: torch-directml (0.2.5.dev240914) 依赖 torch==2.4.1, 与 mizuoto 需要的 torch>=2.8 冲突
"""

TORCH_BACKEND_CHOICES = ["auto", "cuda", "rocm", "xpu", "mps", "cpu"]
"""命令行可选的 PyTorch 类型"""

ENGINE_PACKAGES: dict[str, str] = {
    "fishspeech": "mizuoto-fishspeech",
    "indextts": "mizuoto-indextts",
}
"""许可证受限的 Mizuoto 引擎及其软件包名称

这些引擎使用非自由许可证 (Fish Audio Research License / bilibili Model Use License), 不在 requirements.txt 中,
仅在使用 --engines 指定时安装. 引擎软件包与 mizuoto 使用相同的版本号
"""
