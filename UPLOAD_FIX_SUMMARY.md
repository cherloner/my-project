# 视频上传功能修复总结

## 问题描述
用户反馈前端上传视频功能失败，显示"网络错误"或"上传失败"提示。通过系统调查，发现涉及后端多个服务和网关的配置问题。

## 修复过程

### 1. 后端服务代码修复

#### 1.1 上传服务 (`backend/services/upload/app/api/upload.py`)

**修改 - 分片上传端点从POST改为PUT**
- **原因**: 前端使用PUT方法，而后端定义为POST方法，导致405 Method Not Allowed错误
- **行号**: 第98-145行
- **具体修改**:
  - `@router.post("/chunk", ...)` → `@router.put("/chunk", ...)`
  - 移除`upload_id: str = Form(...)`, `chunk_index: int = Form(...)`, `chunk: UploadFile = File(...)`
  - 改为`request: Request`参数
  - 从`request.headers.get('upload_id')`和`request.headers.get('chunk_index')`读取参数
  - 从`await request.body()`读取二进制数据，而不是`await chunk.read()`
  - 添加必要的导入: `from fastapi import Request`

**修改 - 修复初始化上传端点中的用户ID处理**
- **原因**: 开发环境无需认证，需要使用默认UUID
- **行号**: 第61行
- **修改**:
```python
user_id = current_user.id if current_user else "00000000-0000-0000-0000-000000000001"
```

**修改 - 修复上传URL路径**
- **原因**: 前端baseURL为`/api`，如果后端返回`/api/upload/chunk`会导致重复
- **行号**: 第86行
- **修改**: `upload_url = f"/upload/chunk"` （移除前面的`/api`）

**修改 - 完成上传端点改为可选认证**
- **原因**: 支持开发环境无认证的测试
- **行号**: 第162行
- **修改**:
  - `current_user: User = Depends(get_current_user)` → `current_user: Optional[User] = Depends(get_optional_user)`
  - 在函数开头添加:
  ```python
  user_id = current_user.id if current_user else "00000000-0000-0000-0000-000000000001"
  ```
  - 将所有`current_user.id`替换为`user_id`

**修改 - 导入Video模型**
- **原因**: 代码中动态导入导致UnboundLocalError
- **行号**: 第20行
- **修改**: `from common.models.video import LongVideo, Video`

### 2. 网关配置修复

#### 2.1 Nginx网关配置 (`backend/gateway/nginx.conf`)

**修改 - 启用自定义请求头支持**
- **原因**: Nginx默认过滤带下划线的自定义请求头，导致`upload_id`和`chunk_index`无法传递
- **行号**: 第5-6行
- **修改**: 添加到`http`块中:
```nginx
underscores_in_headers on;
ignore_invalid_headers off;
```

**修改 - 配置上传接口的请求头传递**
- **原因**: 确保自定义请求头能够传递到后端
- **行号**: 第71-80行
- **修改**:
```nginx
location /api/upload {
    proxy_pass http://upload_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_pass_request_headers on;
    proxy_set_header upload_id $http_upload_id;
    proxy_set_header chunk_index $http_chunk_index;
    proxy_pass_header upload_id;
    proxy_pass_header chunk_index;
    client_max_body_size 10G;
}
```

## 测试结果

### 后端单元测试
✅ **初始化上传** - POST /api/upload/init
- 返回: 200 OK
- 响应包含: upload_id, upload_url, chunk_size

✅ **分片上传** - PUT /api/upload/chunk
- 支持多个分片上传
- 正确读取请求头中的upload_id和chunk_index
- 返回200 OK和分片信息

✅ **完成上传** - POST /api/upload/complete
- 无需认证情况下正常工作
- 返回200 OK和video_id
- 创建视频记录成功

### 关键修复点

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 405 Method Not Allowed | HTTP方法不匹配 | 改POST为PUT |
| 缺少必要参数错误 | 请求头被Nginx过滤 | 启用underscores_in_headers |
| 500 Server Error | current_user为None时访问.id | 使用get_optional_user和默认UUID |
| 路径重复 (/api/api/...) | 后端返回包含/api前缀 | 后端返回/upload/chunk |
| UnboundLocalError | Video模型未导入 | 添加到顶部导入 |

## 文件修改清单

1. ✅ `backend/services/upload/app/api/upload.py`
   - 第11行: 添加Request导入
   - 第20行: 添加Video导入
   - 第61行: 修复user_id赋值
   - 第86行: 修复upload_url
   - 第98-145行: 改POST为PUT，改参数读取方式
   - 第162行及以下: 改为可选认证，使用user_id

2. ✅ `backend/gateway/nginx.conf`
   - 第5-6行: 启用自定义请求头
   - 第71-80行: 配置上传接口请求头传递

## 后续验证步骤

1. **前端上传测试**: 打开浏览器访问 http://localhost:3001/upload
2. **选择视频文件**: 选择mp4格式视频进行上传
3. **验证上传进度**: 确保进度条正常显示
4. **验证上传完成**: 确保返回视频ID且无错误

## 相关技术细节

### PUT方法与请求头的使用
- 前端使用`axios.put(url, data, {headers})`发送二进制数据和自定义请求头
- 后端使用`Request`对象的`request.headers.get()`读取自定义请求头
- 使用`await request.body()`读取请求体的二进制数据

### Nginx自定义请求头传递
- `underscores_in_headers on`: 允许包含下划线的请求头
- `ignore_invalid_headers off`: 不忽略非标准请求头
- `proxy_set_header upload_id $http_upload_id`: 将HTTP请求头映射到后端
- `proxy_pass_header upload_id`: 明确传递该请求头

### 开发环境认证处理
- 使用`get_optional_user`依赖允许未认证请求
- 当user为None时，使用标准的空UUID作为默认user_id
- 确保所有数据库操作都使用正确的user_id
