"""启动文件"""

import sys

if not (3, 10) <= sys.version_info[:2] <= (3, 13):
    print(f"Mizuoto TTS WebUI 需要 Python 3.10 ~ 3.13, 当前版本为 {sys.version.split()[0]}")
    sys.exit(1)

from mizuoto_tts_webui import main

if __name__ == "__main__":
    main()
