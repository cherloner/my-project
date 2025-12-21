#!/usr/bin/env python3
"""
短视频学习平台 - 完整后端服务
集成视频切分、内容推荐、用户互动等核心功能
"""

import os
import sys
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(project_root)

# 导入数据库和模型
from .database import SessionLocal, engine, init_db

# 导入API路由
from .api.auth import router as auth_router
from .api.video import router as video_router
from .api.split import router as split_router
from .api.feed import router as feed_router
from .api.interaction import router as interaction_router

# 初始化数据库
init_db()

# 创建FastAPI应用
app = FastAPI(
    title="短视频学习平台API",
    version="1.0.0",
    description="智能视频切分与短视频学习平台后端服务",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(auth_router)
app.include_router(video_router)
app.include_router(split_router)
app.include_router(feed_router)
app.include_router(interaction_router)

# 确保必要的目录存在
def setup_directories():
    directories = ["videos", "output", "output_keyframes", "output_splited_videos", "saved_videos"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    setup_directories()
    print("✅ 短视频学习平台后端服务已启动")
    print("   - 服务地址: http://localhost:8001")
    print("   - API文档: http://localhost:8001/docs")
    print("\n📱 可用功能:")
    print("   🔐 用户认证 (JWT + 手机验证码)")
    print("   📹 视频上传与管理")
    print("   🧩 智能视频切分 (5步AI流程)")
    print("   📱 短视频推荐流")
    print("   🔍 视频搜索")
    print("   ❤️ 点赞/收藏/评论")
    print("   📊 热门视频排行")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "短视频学习平台后端服务",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "available_endpoints": {
            "认证": ["/auth/send-code", "/auth/login", "/auth/profile"],
            "视频": ["/videos/upload/init", "/videos/upload/chunk", "/videos/upload/complete"],
            "切分": ["/split/tasks", "/split/tasks/{task_id}", "/split/tasks/{task_id}/segments"],
            "内容流": ["/feed/recommend", "/feed/following", "/feed/hot", "/feed/search"],
            "互动": ["/interaction/like", "/interaction/favorite", "/interaction/comment"]
        }
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "short-video-learning-platform",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动短视频学习平台后端服务...")
    print(f"   服务地址: http://localhost:8001")
    print(f"   API文档: http://localhost:8001/docs")
    print("-" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)