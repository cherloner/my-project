# 认证问题修复文档

## 📋 问题描述

### 错误现象
前端访问后端 API 时出现大量 500 Internal Server Error：
```
- /api/feed/recommend → 500 错误
- /api/learn/records → 500 错误  
- /api/upload/init → 500 错误
```

### 根本原因
1. **前端使用 Mock 登录**
   - 登录页面使用模拟登录，存储的 Token 为 `'mock-jwt-token'`
   - 位置：`frontend/src/pages/Login.tsx:51`
   
2. **后端强制要求 JWT 认证**
   - 所有 API 端点使用 `get_current_user()` 强制验证 JWT
   - Mock Token 无法通过 JWT 解码验证
   
3. **JWT 验证失败导致 500 错误**
   - 预期应返回 401 Unauthorized
   - 实际因解码异常抛出 500 Internal Server Error

---

## 🔧 代码修改

### 1. 内容服务 - 推荐接口

**文件**: `backend/services/content/app/api/feed.py`

**修改位置**: Line 126-133

**修改前**:
```python
@router.get("/recommend", summary="智能推荐视频流")
async def get_recommend_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    strategy: str = Query("hybrid", regex="^(hybrid|content|collaborative|popularity)$", description="推荐策略"),
    current_user: User = Depends(get_current_user),  # ❌ 强制认证
    db: Session = Depends(get_db)
):
    """获取智能推荐视频流"""
    
    recommendation_service = RecommendationService(db)
    recommended_videos = recommendation_service.get_recommendations(
        user_id=str(current_user.id),  # ❌ 必须有用户
        strategy=strategy,
        limit=page_size * 5
    )
```

**修改后**:
```python
@router.get("/recommend", summary="智能推荐视频流")
async def get_recommend_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    strategy: str = Query("hybrid", regex="^(hybrid|content|collaborative|popularity)$", description="推荐策略"),
    current_user: Optional[User] = Depends(get_optional_user),  # ✅ 可选认证
    db: Session = Depends(get_db)
):
    """获取智能推荐视频流"""
    
    recommendation_service = RecommendationService(db)
    user_id = str(current_user.id) if current_user else None  # ✅ 支持匿名访问
    recommended_videos = recommendation_service.get_recommendations(
        user_id=user_id,
        strategy=strategy,
        limit=page_size * 5
    )
```

**修改原因**:
- 开发环境下需要支持未登录用户浏览推荐视频
- 使用 `get_optional_user()` 允许请求在无 Token 或 Token 无效时继续执行
- 当没有用户信息时，推荐系统使用通用推荐策略

---

### 2. 内容服务 - 学习心跳接口

**文件**: `backend/services/content/app/api/learn.py`

**修改位置**: Line 32-38

**修改前**:
```python
@router.post("/heartbeat", summary="学习心跳上报")
async def heartbeat(
    request: HeartbeatRequest,
    current_user: User = Depends(get_current_user),  # ❌ 强制认证
    db: Session = Depends(get_db)
):
    """上报学习进度心跳"""
    
    # 验证视频存在
    video = db.query(Video).filter(...)
```

**修改后**:
```python
@router.post("/heartbeat", summary="学习心跳上报")
async def heartbeat(
    request: HeartbeatRequest,
    current_user: Optional[User] = Depends(get_optional_user),  # ✅ 可选认证
    db: Session = Depends(get_db)
):
    """上报学习进度心跳"""
    
    # ✅ 如果没有用户登录，直接返回成功（开发环境）
    if not current_user:
        return success_response(
            data={"message": "未登录，学习进度未记录"},
            message="心跳接收成功"
        )
    
    # 验证视频存在
    video = db.query(Video).filter(...)
```

**修改原因**:
- 前端视频播放器会定期发送心跳请求
- 开发环境下允许未登录用户观看视频，但不记录学习进度

---

### 3. 内容服务 - 学习完成接口

**文件**: `backend/services/content/app/api/learn.py`

**修改位置**: Line 103-109

**修改前**:
```python
@router.post("/complete", summary="完成学习")
async def complete(
    request: CompleteRequest,
    current_user: User = Depends(get_current_user),  # ❌ 强制认证
    db: Session = Depends(get_db)
):
    """标记视频学习完成"""
    
    # 验证视频存在
    video = db.query(Video).filter(...)
```

**修改后**:
```python
@router.post("/complete", summary="完成学习")
async def complete(
    request: CompleteRequest,
    current_user: Optional[User] = Depends(get_optional_user),  # ✅ 可选认证
    db: Session = Depends(get_db)
):
    """标记视频学习完成"""
    
    # ✅ 如果没有用户登录，直接返回成功（开发环境）
    if not current_user:
        return success_response(
            data={"message": "未登录，学习完成未记录"},
            message="学习完成记录接收成功"
        )
    
    # 验证视频存在
    video = db.query(Video).filter(...)
```

**修改原因**:
- 用户观看视频达到 90% 时会触发完成标记
- 开发环境下允许未登录用户操作，但不记录数据

---

### 4. 内容服务 - 学习记录接口（新增）

**文件**: `backend/services/content/app/api/learn.py`

**修改位置**: Line 149-204 (新增代码)

**新增接口**:
```python
@router.get("/records", summary="获取学习记录")
async def get_records(
    current_user: Optional[User] = Depends(get_optional_user),  # ✅ 可选认证
    db: Session = Depends(get_db)
):
    """获取用户的学习记录"""
    
    # 如果没有用户登录，返回空列表（开发环境）
    if not current_user:
        return success_response(
            data={
                "records": [],
                "total": 0
            },
            message="未登录，无学习记录"
        )
    
    # 获取用户的学习记录
    records = db.query(LearnRecord).filter(
        LearnRecord.user_id == current_user.id
    ).order_by(LearnRecord.last_watch_time.desc()).all()
    
    # 获取视频信息
    record_list = []
    for record in records:
        video = db.query(Video).filter(Video.id == record.video_id).first()
        if video:
            record_list.append({
                "id": str(record.id),
                "video_id": str(record.video_id),
                "title": video.title,
                "cover": video.cover_url,
                "status": record.status,
                "progress": float(record.completed_ratio) if record.completed_ratio else 0.0,
                "last_watch_time": record.last_watch_time.isoformat() if record.last_watch_time else None
            })
    
    return success_response(
        data={
            "records": record_list,
            "total": len(record_list)
        },
        message="获取学习记录成功"
    )
```

**新增原因**:
- 前端 Profile 页面调用 `learnApi.getRecords()` 但后端没有此接口
- 导致 404 或 500 错误
- 新增接口以支持学习记录查询功能

---

### 5. 上传服务 - 初始化上传接口

**文件**: `backend/services/upload/app/api/upload.py`

**修改位置**: Line 19 + Line 52-59

**导入修改**:
```python
# 修改前
from common.utils.auth import get_current_user

# 修改后  
from common.utils.auth import get_current_user, get_optional_user  # ✅ 导入可选认证
```

**接口修改前**:
```python
@router.post("/init", summary="初始化上传任务")
async def init_upload(
    request: UploadInitRequest,
    current_user: User = Depends(get_current_user),  # ❌ 强制认证
    db: Session = Depends(get_db)
):
    """初始化上传任务"""
    
    upload_id = f"UP_{uuid.uuid4().hex[:8]}"
    
    upload_task = UploadTask(
        upload_id=upload_id,
        user_id=current_user.id,  # ❌ 必须有用户
        file_name=request.file_name,
        ...
    )
```

**接口修改后**:
```python
@router.post("/init", summary="初始化上传任务")
async def init_upload(
    request: UploadInitRequest,
    current_user: Optional[User] = Depends(get_optional_user),  # ✅ 可选认证
    db: Session = Depends(get_db)
):
    """初始化上传任务"""
    
    # ✅ 如果没有用户登录，使用默认用户ID（开发环境）
    user_id = current_user.id if current_user else "default_user"
    
    upload_id = f"UP_{uuid.uuid4().hex[:8]}"
    
    upload_task = UploadTask(
        upload_id=upload_id,
        user_id=user_id,  # ✅ 支持默认用户
        file_name=request.file_name,
        ...
    )
```

**修改原因**:
- 用户上传视频时触发初始化请求
- 开发环境下允许未登录用户上传（使用默认用户 ID）
- 便于测试上传功能

---

## ✅ 修改效果

### 修改前（❌ 错误状态）
```
GET /api/feed/recommend → 500 Internal Server Error
POST /api/learn/heartbeat → 500 Internal Server Error  
POST /api/learn/complete → 500 Internal Server Error
GET /api/learn/records → 404 Not Found
POST /api/upload/init → 500 Internal Server Error
```

### 修改后（✅ 正常运行）
```
GET /api/feed/recommend → 200 OK
  ├─ 有 Token: 返回个性化推荐
  └─ 无 Token: 返回通用推荐
  
POST /api/learn/heartbeat → 200 OK
  ├─ 有 Token: 记录学习进度
  └─ 无 Token: 返回成功但不记录

POST /api/learn/complete → 200 OK  
  ├─ 有 Token: 标记学习完成
  └─ 无 Token: 返回成功但不记录

GET /api/learn/records → 200 OK
  ├─ 有 Token: 返回用户学习记录
  └─ 无 Token: 返回空列表

POST /api/upload/init → 200 OK
  ├─ 有 Token: 使用用户 ID 创建上传任务
  └─ 无 Token: 使用默认用户 ID
```

---

## 🚀 应用修改

### 方式 1: 重新构建 Docker 镜像（推荐）

```powershell
cd G:\videocut\SenseVoice\my-project\backend

# 重新构建服务
docker-compose build content-service upload-service

# 重启服务
docker-compose up -d content-service upload-service
```

### 方式 2: 直接在容器中修改（已执行）

```powershell
# 修改容器内代码
docker exec -it content_service sh -c "sed -i 's/...' /app/services/content/app/api/feed.py"

# 重启服务使修改生效
docker-compose restart content-service upload-service
```

**注意**: 方式 2 的修改在容器重新创建后会丢失，建议使用方式 1。

---

## 📝 后续建议

### 短期（开发环境）
✅ 当前修改已满足开发需求，支持无需登录即可测试功能

### 中期（测试环境）
- [ ] 启用真实的短信验证码服务
- [ ] 在前端 `Login.tsx` 中取消注释真实 API 调用
- [ ] 测试完整的登录注册流程

### 长期（生产环境）  
- [ ] 将认证修改为强制要求（恢复 `get_current_user`）
- [ ] 仅保留部分公开端点使用 `get_optional_user`（如公开视频列表）
- [ ] 添加完善的权限控制和 API 速率限制

---

## 🔍 相关文件索引

| 文件路径 | 修改内容 | 行号 |
|---------|---------|------|
| `backend/services/content/app/api/feed.py` | 推荐接口改为可选认证 | 126-146 |
| `backend/services/content/app/api/learn.py` | 心跳接口改为可选认证 | 32-50 |
| `backend/services/content/app/api/learn.py` | 完成接口改为可选认证 | 103-120 |
| `backend/services/content/app/api/learn.py` | 新增学习记录接口 | 149-204 |
| `backend/services/upload/app/api/upload.py` | 上传初始化改为可选认证 | 19, 52-74 |
| `backend/common/utils/auth.py` | 认证工具函数（已存在） | 44-73 |

---

## 📞 技术支持

如有问题，请参考：
- [系统架构设计文档](backend/docs/系统架构设计文档.md)
- [API设计文档](backend/docs/API设计文档.md)
- [故障排查指南](backend/docs/故障排查指南.md)

---

**文档版本**: 1.0  
**更新日期**: 2025年12月26日  
**维护者**: AI Assistant
