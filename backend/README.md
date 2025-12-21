# 短视频学习平台 - 后端服务

完整的短视频学习平台后端，基于 FastAPI + SQLAlchemy + Celery 构建，集成智能视频切分和短视频社交功能。

## 🚀 快速启动

### 方式一：本地开发模式

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python start_platform.py
```

### 方式二：Docker 部署（推荐）

```bash
# 在工作区根目录运行
cd my-project-dev
docker-compose up --build
```

## 📍 服务信息

- **服务地址**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: `GET /api/health`

## 🎯 核心功能模块

### 1. 🔐 用户认证系统
- 手机号验证码登录/注册
- JWT Token 认证
- 用户资料管理
- 角色权限控制

### 2. 📹 视频上传与管理
- 分片上传（支持大文件）
- 视频元数据管理
- 长视频/短视频分类
- 课程视频关联

### 3. 🧩 智能视频切分
**5步AI处理流程：**
1. MP4转WAV - 音频提取
2. 语音转文字 - SenseVoice模型
3. 关键帧提取 - 智能场景检测
4. 知识点分析 - GLM-4.5V多模态分析
5. 视频分割 - 基于知识点边界

### 4. 📱 短视频内容流
- **推荐流** - 个性化视频推荐
- **关注流** - 关注用户视频
- **热门流** - 按热度排序
- **搜索功能** - 标题/标签/作者搜索

### 5. ❤️ 用户互动系统
- 点赞/取消点赞
- 收藏/取消收藏
- 评论/回复评论
- 用户互动记录

### 6. 📊 学习与统计
- 观看记录跟踪
- 学习进度管理
- 视频统计信息
- 用户行为分析

## 📋 API 接口概览

### 认证相关
- `POST /auth/send-code` - 发送验证码
- `POST /auth/login` - 手机号登录
- `GET /auth/profile` - 获取用户资料
- `PUT /auth/profile` - 更新用户资料

### 视频相关
- `POST /videos/upload/init` - 初始化上传
- `POST /videos/upload/chunk/{upload_id}/{chunk_index}` - 上传分片
- `POST /videos/upload/complete/{upload_id}` - 完成上传
- `GET /videos/` - 获取视频列表
- `GET /videos/{video_id}` - 获取视频详情

### 切分相关
- `POST /split/tasks` - 创建切分任务
- `GET /split/tasks` - 获取任务列表
- `GET /split/tasks/{task_id}` - 获取任务详情
- `GET /split/tasks/{task_id}/segments` - 获取切分结果

### 内容流相关
- `GET /feed/recommend` - 推荐视频流
- `GET /feed/following` - 关注用户视频流
- `GET /feed/hot` - 热门视频
- `GET /feed/search` - 搜索视频
- `GET /feed/video/{video_id}` - 获取视频详情

### 互动相关
- `POST /interaction/like` - 点赞/取消点赞
- `POST /interaction/favorite` - 收藏/取消收藏
- `POST /interaction/comment` - 发表评论
- `GET /interaction/video/{video_id}/comments` - 获取评论列表

## 🏗️ 技术架构

### 核心技术栈
- **框架**: FastAPI + SQLAlchemy + Celery
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **缓存**: Redis
- **认证**: JWT + 手机验证码
- **消息队列**: Celery + Redis

### 微服务架构
- **API Gateway** - 统一入口
- **Auth Service** - 认证服务
- **Content Service** - 内容服务
- **Split Service** - 切分服务
- **Course Service** - 课程服务

## 🔧 开发与部署

### 数据库初始化
```sql
-- 使用 my-project-dev/database/init.sql 初始化数据库
```

### 环境配置
复制 `.env.example` 为 `.env` 并配置相关参数：
```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/videocut

# JWT配置
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 短信服务配置（可选）
SMS_API_KEY=your-sms-api-key

# AI模型配置
GLM_API_KEY=your-glm-api-key
```

### 性能优化
- 视频处理使用异步任务
- 数据库查询优化和索引
- Redis 缓存热点数据
- CDN 加速视频分发

## 📈 监控与日志

- 健康检查端点: `/api/health`
- 结构化日志输出
- 错误监控和告警
- 性能指标收集

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码变更
4. 创建 Pull Request

## 📄 许可证

MIT License
