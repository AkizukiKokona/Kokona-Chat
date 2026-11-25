#!/usr/bin/env python3
"""启动入口：python3 run.py

环境变量（都有默认值，见 kokona_chat/config.py）：
  CHAT_BASE      站点前缀，默认 /chat（用 chat 子域名时设为空字符串）
  CHAT_PORT      监听端口，默认 8299
  CHAT_DATA_DIR  数据目录，默认 ./data
  CHAT_SMTP_*    发信配置（不配也能跑，验证码会在管理后台可见）
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kokona_chat.server import serve  # noqa: E402

if __name__ == "__main__":
    serve()
