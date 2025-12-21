#!/usr/bin/env python3
"""
简单启动脚本 - 解决 Windows 下 uvicorn 启动问题
"""

import os
import sys

# 设置工作目录
backend_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(backend_dir, 'app')
os.chdir(backend_dir)

# 添加项目路径
sys.path.insert(0, backend_dir)
sys.path.insert(0, app_dir)

# 导入应用
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动短视频学习平台后端服务...")
    print("服务地址: http://localhost:8001")
    print("API文档: http://localhost:8001/docs")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    
    # 最简单的启动方式，避免 Windows 下的问题
    uvicorn.run(
        "app.main:app",  # 使用字符串导入方式
        host="0.0.0.0",
        port=8001,
        reload=False,    # 禁用热重载
        log_level="info"
    )