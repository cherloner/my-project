# 智能视频剪辑与内容推荐系统

一个基于AI的智能视频剪辑平台，集成了SenseVoice语音识别、智能内容分割和个性化推荐系统。

## 🎯 项目特色

### 🤖 AI智能处理
- **SenseVoice语音识别** - 高精度语音转文字
- **智能场景检测** - 基于内容的关键帧提取
- **多模态分析** - 结合视觉和文本信息的知识点识别
- **个性化推荐** - 多种推荐算法混合的智能内容推荐

### 📹 视频处理能力
- **长视频智能分割** - 自动识别知识点边界
- **关键帧提取** - 智能场景切换检测
- **格式转换** - 支持多种视频格式处理
- **批量处理** - 高效处理大量视频内容

### 🎨 内容推荐系统
- **内容相似度推荐** - 基于视频特征的相似内容推荐
- **协同过滤** - 基于用户行为的个性化推荐
- **热度推荐** - 热门内容智能推送
- **混合推荐** - 多种算法组合的优化推荐

## 🚀 快速开始

### 环境要求
- Python 3.8+
- FFmpeg
- Git LFS (用于大模型文件)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/cherloner/videocut.git
cd videocut
```

2. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

3. **配置环境**
```bash
# 复制环境配置文件
cp .env.example .env
# 编辑配置文件，设置相关参数
```

4. **启动服务**
```bash
python run_server.py
```

### Docker 部署（推荐）
```bash
cd my-project-dev
docker-compose up --build
```

## 📁 项目结构

```
videocut/
├── backend/                 # 后端服务
│   ├── app/                # 应用核心模块
│   │   ├── api/           # API接口
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务服务
│   │   └── recommendation.py # 推荐系统
│   ├── requirements.txt    # Python依赖
│   └── run_server.py      # 服务启动脚本
├── SenseVoiceSmall/        # SenseVoice模型文件
│   ├── model.pt           # 语音识别模型
│   └── README.md          # 模型说明
├── utils/                  # 工具模块
│   ├── ctc_alignment.py   # 语音对齐工具
│   └── infer_utils.py     # 推理工具
├── database/               # 数据库相关
│   └── init.sql           # 数据库初始化脚本
├── my-project-dev/         # 开发配置
│   ├── docker-compose.yml # Docker编排
│   └── 系统架构设计文档.md  # 架构文档
└── videos/                 # 视频文件目录
```

## 🔧 核心功能

### 1. 智能视频切分

**5步处理流程：**
1. **音频提取** - MP4转WAV格式
2. **语音识别** - SenseVoice模型转文字
3. **关键帧检测** - 智能场景切换识别
4. **知识点分析** - 多模态内容理解
5. **视频分割** - 基于知识点边界切分

### 2. 内容推荐系统

**推荐策略：**
- **内容相似度推荐** - 基于视频特征向量计算相似度
- **协同过滤推荐** - 基于用户历史行为推荐
- **热度推荐** - 按播放量、点赞数等指标推荐
- **混合推荐** - 多种算法加权组合优化

### 3. API接口

**主要端点：**
- `POST /split/tasks` - 创建视频切分任务
- `GET /feed/recommend` - 获取推荐视频流
- `GET /feed/hot` - 获取热门视频
- `POST /interaction/like` - 点赞/取消点赞
- `GET /videos/{video_id}` - 获取视频详情

## 🛠️ 技术架构

### 后端技术栈
- **Web框架**: FastAPI
- **数据库**: SQLAlchemy + SQLite/PostgreSQL
- **任务队列**: Celery + Redis
- **认证**: JWT Token
- **文件存储**: 本地文件系统 + CDN

### AI模型集成
- **语音识别**: SenseVoice Small模型
- **文本处理**: 中文分词和语义分析
- **视觉分析**: OpenCV场景检测
- **推荐算法**: 多种机器学习算法

## 📊 性能指标

- **语音识别准确率**: >95%
- **场景检测准确率**: >90%
- **推荐系统召回率**: >85%
- **API响应时间**: <200ms
- **并发处理能力**: 支持多任务并行

## 🔒 安全特性

- JWT Token认证
- 文件上传安全校验
- SQL注入防护
- 敏感数据加密
- 访问权限控制

## 📈 部署说明

### 开发环境
```bash
# 本地开发模式
cd backend
python run_server.py
```

### 生产环境
```bash
# 使用Docker部署
cd my-project-dev
docker-compose -f docker-compose.prod.yml up -d
```

### 环境变量配置
```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/videocut

# JWT配置
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI服务配置
GLM_API_KEY=your-glm-api-key
SENSEVOICE_MODEL_PATH=./SenseVoiceSmall/model.pt
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- **项目作者**: cherloner
- **邮箱**: 1844390881@qq.com
- **GitHub**: [https://github.com/cherloner](https://github.com/cherloner)

## 🙏 致谢

- [SenseVoice](https://github.com/SenseVoice) - 语音识别模型
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理工具

---

⭐ 如果这个项目对你有帮助，请给我们一个star！