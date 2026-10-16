"""运行环境检查

分为两个阶段:

1. PyTorch: 未安装 (或版本低于 Mizuoto 的要求) 时根据显卡类型和系统安装对应的 PyTorch
2. 项目依赖: 检查 requirements.txt 中的依赖 (包括 mizuoto) 及 mizuoto 自身声明的依赖, 缺失时进行安装
3. 许可证受限的引擎: 检查使用 --engines 指定的引擎及已安装的引擎, 缺失或与 mizuoto 版本不一致时进行安装
"""

import importlib
import os
import sys

from mizuoto_tts_webui.cmd_runner import run_cmd
from mizuoto_tts_webui.config import (
    ENGINE_PACKAGES,
    LOGGER_COLOR,
    LOGGER_LEVEL,
    LOGGER_NAME,
    PYTORCH_INSTALL_ARGS,
    REQUIREMENTS_PATH,
    TORCH_MIN_VERSION,
)
from mizuoto_tts_webui.gpu_detector import detect_torch_backend
from mizuoto_tts_webui.logger import get_logger
from mizuoto_tts_webui.package_analyzer import (
    get_package_version_from_library,
    is_package_installed,
    validate_package_metadata_dependencies,
    validate_requirements,
)

logger = get_logger(
    name=LOGGER_NAME,
    level=LOGGER_LEVEL,
    color=LOGGER_COLOR,
)

TORCH_REQUIREMENT = f"torch>={TORCH_MIN_VERSION}"
"""Mizuoto 需要的 PyTorch 版本"""


def pip_install(
    *args: str,
) -> None:
    """使用当前 Python 解释器的 Pip 安装 Python 软件包

    Args:
        *args (str):
            传递给 ``pip install`` 的参数

    Raises:
        RuntimeError:
            安装失败时
    """
    custom_env = os.environ.copy()
    custom_env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    run_cmd([sys.executable, "-m", "pip", "install", *args], custom_env=custom_env, shell=False)
    importlib.invalidate_caches()


def check_pytorch(
    backend: str = "auto",
    reinstall: bool = False,
) -> None:
    """检查 PyTorch, 未安装时根据显卡类型安装

    Args:
        backend (str):
            PyTorch 类型, ``auto`` 为自动检测
        reinstall (bool):
            卸载已安装的 PyTorch 并重新安装

    Raises:
        RuntimeError:
            PyTorch 安装失败时
    """
    logger.info("检查 PyTorch 中")
    if reinstall:
        logger.info("卸载原有 PyTorch 中")
        run_cmd([sys.executable, "-m", "pip", "uninstall", "torch", "-y"], shell=False, check=False)
        importlib.invalidate_caches()
    elif is_package_installed(TORCH_REQUIREMENT):
        logger.info("PyTorch 已安装")
        return
    elif is_package_installed("torch"):
        logger.warning("已安装的 PyTorch 版本低于 Mizuoto 需要的 %s, 将重新安装 PyTorch", TORCH_MIN_VERSION)

    if backend == "auto":
        backend = detect_torch_backend()
    logger.info("安装 PyTorch 中, 类型: %s", backend)

    pip_install(*PYTORCH_INSTALL_ARGS[backend])
    if not is_package_installed(TORCH_REQUIREMENT):
        raise RuntimeError("PyTorch 安装后仍未满足版本要求, 请检查上方的 Pip 输出")
    logger.info("PyTorch 安装完成")


def _requirements_satisfied() -> bool:
    """检查项目依赖及 mizuoto 自身声明的依赖是否完整

    Returns:
        bool:
            依赖完整时返回 True
    """
    if not validate_requirements(REQUIREMENTS_PATH):
        return False
    # requirements.txt 只记录顶层依赖, mizuoto 的依赖缺失 / 损坏时也需要重新安装
    return validate_package_metadata_dependencies("mizuoto")


def check_requirements(
    index_url: str | None = None,
) -> None:
    """检查项目依赖, 缺失时进行安装

    Args:
        index_url (str | None):
            安装依赖时使用的 PyPI 镜像地址

    Raises:
        FileNotFoundError:
            依赖记录文件不存在时
        RuntimeError:
            依赖安装失败时
    """
    if not REQUIREMENTS_PATH.is_file():
        raise FileNotFoundError(f"在 {REQUIREMENTS_PATH} 中未找到依赖记录文件, 请检查项目文件是否完整")

    logger.info("检查 Mizuoto TTS WebUI 依赖中")
    if _requirements_satisfied():
        logger.info("Mizuoto TTS WebUI 依赖完整")
        return

    logger.info("安装 Mizuoto TTS WebUI 依赖中")
    args = ["-r", REQUIREMENTS_PATH.as_posix()]
    if index_url:
        args += ["--index-url", index_url]
    pip_install(*args)
    if not _requirements_satisfied():
        raise RuntimeError("Mizuoto TTS WebUI 依赖安装后仍不完整, 请检查上方的 Pip 输出")
    logger.info("Mizuoto TTS WebUI 依赖安装完成")


def _engines_satisfied(
    requirements: dict[str, str],
) -> bool:
    """检查引擎软件包及其自身声明的依赖是否完整

    Args:
        requirements (dict[str, str]):
            引擎软件包名称到版本要求的映射

    Returns:
        bool:
            依赖完整时返回 True
    """
    return all(
        is_package_installed(requirement) and validate_package_metadata_dependencies(package)
        for package, requirement in requirements.items()
    )


def check_engines(
    engines: list[str],
    index_url: str | None = None,
) -> None:
    """检查许可证受限的引擎, 缺失或与 mizuoto 版本不一致时进行安装

    需要在 mizuoto 安装完成后调用. 除了指定的引擎, 已安装的引擎也会被检查, 避免 mizuoto 更新后引擎版本不一致

    Args:
        engines (list[str]):
            需要安装的引擎, 为 ``config.ENGINE_PACKAGES`` 中的键
        index_url (str | None):
            安装引擎时使用的 PyPI 镜像地址

    Raises:
        RuntimeError:
            mizuoto 未安装或引擎安装失败时
    """
    packages = [
        package for name, package in ENGINE_PACKAGES.items() if name in engines or get_package_version_from_library(package) is not None
    ]
    if not packages:
        return

    mizuoto_version = get_package_version_from_library("mizuoto")
    if mizuoto_version is None:
        raise RuntimeError("未安装 Mizuoto, 无法安装引擎")
    # 引擎软件包与 mizuoto 一同发布, 版本号相同, mizuoto 不会检查引擎的版本
    requirements = {package: f"{package}=={mizuoto_version}" for package in packages}

    logger.info("检查引擎中: %s", ", ".join(packages))
    if _engines_satisfied(requirements):
        logger.info("引擎完整")
        return

    logger.info("安装引擎中")
    args = list(requirements.values())
    if index_url:
        args += ["--index-url", index_url]
    pip_install(*args)
    if not _engines_satisfied(requirements):
        raise RuntimeError("引擎安装后仍不完整, 请检查上方的 Pip 输出")
    logger.info("引擎安装完成, 下载模型前需要在 WebUI 中接受引擎的许可证")


def check_environment(
    backend: str = "auto",
    reinstall_torch: bool = False,
    index_url: str | None = None,
    engines: list[str] | None = None,
) -> None:
    """依次检查 PyTorch, 项目依赖和引擎

    Args:
        backend (str):
            PyTorch 类型, ``auto`` 为自动检测
        reinstall_torch (bool):
            重新安装 PyTorch
        index_url (str | None):
            安装项目依赖和引擎时使用的 PyPI 镜像地址
        engines (list[str] | None):
            需要安装的许可证受限的引擎

    Raises:
        FileNotFoundError:
            依赖记录文件不存在时
        RuntimeError:
            依赖安装失败时
    """
    check_pytorch(backend=backend, reinstall=reinstall_torch)
    check_requirements(index_url=index_url)
    check_engines(engines=engines or [], index_url=index_url)
