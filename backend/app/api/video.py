import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import User, Video, UploadTask, LongVideo, Course, CourseVideo
from .auth import verify_token

router = APIRouter(prefix="/videos", tags=["videos"])

security = HTTPBearer()


class VideoUploadRequest(BaseModel):
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    language: str = "zh-CN"
    video_type: str = "short"
    course_id: Optional[str] = None
    segment_index: Optional[int] = None


class VideoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    tags: Optional[List[str]]
    duration: int
    play_url: str
    cover_url: Optional[str]
    language: str
    status: str
    video_type: str
    author_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UploadTaskResponse(BaseModel):
    upload_id: str
    file_name: str
    file_size: int
    status: str
    completed_chunks: List[int]
    created_at: datetime

    class Config:
        from_attributes = True


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    user_id = verify_token(credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/upload/init", response_model=UploadTaskResponse, summary="初始化视频上传")
async def init_upload(
    file_name: str = Form(...),
    file_size: int = Form(...),
    duration: Optional[int] = Form(None),
    video_type: str = Form("short"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """初始化视频上传任务"""
    
    # 生成上传ID
    upload_id = str(uuid.uuid4())
    
    # 创建上传任务
    upload_task = UploadTask(
        upload_id=upload_id,
        user_id=current_user.id,
        file_name=file_name,
        file_size=file_size,
        duration=duration,
        video_type=video_type,
        status="uploading",
        completed_chunks=[]
    )
    
    db.add(upload_task)
    db.commit()
    db.refresh(upload_task)
    
    return UploadTaskResponse.from_orm(upload_task)


@router.post("/upload/chunk/{upload_id}/{chunk_index}", summary="上传视频分片")
async def upload_chunk(
    upload_id: str,
    chunk_index: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传视频分片"""
    
    # 验证上传任务
    upload_task = db.query(UploadTask).filter(
        UploadTask.upload_id == upload_id,
        UploadTask.user_id == current_user.id
    ).first()
    
    if not upload_task:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    
    if upload_task.status != "uploading":
        raise HTTPException(status_code=400, detail="上传任务状态异常")
    
    # 检查分片是否已上传
    if chunk_index in upload_task.completed_chunks:
        raise HTTPException(status_code=400, detail="分片已上传")
    
    # TODO: 实际项目中需要将分片保存到云存储
    # 这里模拟保存分片
    
    # 更新已完成分片列表
    if upload_task.completed_chunks is None:
        upload_task.completed_chunks = []
    
    upload_task.completed_chunks.append(chunk_index)
    
    # 检查是否所有分片都已完成
    # 这里简化逻辑，实际需要根据文件大小和分片大小计算总分片数
    total_chunks = (upload_task.file_size + 1024 * 1024 - 1) // (1024 * 1024)  # 1MB分片
    if len(upload_task.completed_chunks) >= total_chunks:
        upload_task.status = "completed"
    
    db.commit()
    
    return {"message": "分片上传成功", "chunk_index": chunk_index}


@router.post("/upload/complete/{upload_id}", response_model=VideoResponse, summary="完成视频上传")
async def complete_upload(
    upload_id: str,
    request: VideoUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成视频上传并创建视频记录"""
    
    # 验证上传任务
    upload_task = db.query(UploadTask).filter(
        UploadTask.upload_id == upload_id,
        UploadTask.user_id == current_user.id
    ).first()
    
    if not upload_task:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    
    if upload_task.status != "completed":
        raise HTTPException(status_code=400, detail="上传未完成")
    
    # 创建视频记录
    video = Video(
        author_id=current_user.id,
        title=request.title,
        description=request.description,
        tags=request.tags,
        duration=upload_task.duration or 0,
        play_url=f"/videos/{upload_id}/play",  # 实际项目中应为云存储URL
        cover_url=f"/videos/{upload_id}/cover",  # 实际项目中应为封面图URL
        language=request.language,
        status="pending",
        video_type=request.video_type
    )
    
    # 如果是长视频，创建长视频记录
    if request.video_type == "long":
        db.add(video)
        db.flush()  # 获取video.id
        
        long_video = LongVideo(
            video_id=video.id,
            original_duration=upload_task.duration or 0,
            original_file_url=f"/videos/{upload_id}/original"
        )
        db.add(long_video)
    
    # 如果是课程视频，关联课程
    if request.course_id and request.segment_index is not None:
        course = db.query(Course).filter(Course.course_id == request.course_id).first()
        if course:
            db.add(video)
            db.flush()
            
            course_video = CourseVideo(
                course_id=course.id,
                video_id=video.id,
                segment_index=request.segment_index
            )
            db.add(course_video)
            
            # 更新课程统计信息
            course.total_videos += 1
            course.total_duration += upload_task.duration or 0
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # 更新上传任务状态
    upload_task.status = "processed"
    db.commit()
    
    return VideoResponse.from_orm(video)


@router.get("/", response_model=List[VideoResponse], summary="获取视频列表")
async def get_videos(
    page: int = 1,
    page_size: int = 20,
    video_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取视频列表"""
    
    query = db.query(Video).filter(Video.status == "approved")
    
    if video_type:
        query = query.filter(Video.video_type == video_type)
    
    videos = query.order_by(Video.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return [VideoResponse.from_orm(video) for video in videos]


@router.get("/{video_id}", response_model=VideoResponse, summary="获取视频详情")
async def get_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取视频详情"""
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    return VideoResponse.from_orm(video)


@router.get("/my", response_model=List[VideoResponse], summary="获取我的视频")
async def get_my_videos(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的视频"""
    
    videos = db.query(Video).filter(
        Video.author_id == current_user.id
    ).order_by(Video.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return [VideoResponse.from_orm(video) for video in videos]


@router.put("/{video_id}", response_model=VideoResponse, summary="更新视频信息")
async def update_video(
    video_id: str,
    request: VideoUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新视频信息"""
    
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.author_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在或无权操作")
    
    # 更新可修改的字段
    video.title = request.title
    video.description = request.description
    video.tags = request.tags
    video.language = request.language
    
    db.commit()
    db.refresh(video)
    
    return VideoResponse.from_orm(video)


@router.delete("/{video_id}", summary="删除视频")
async def delete_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除视频"""
    
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.author_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在或无权操作")
    
    # 实际项目中需要删除云存储中的文件
    # 这里只删除数据库记录
    
    db.delete(video)
    db.commit()
    
    return {"message": "视频删除成功"}


# 简化上传接口 - 用于前端演示
import os
import logging
from fastapi import UploadFile, File, Depends
from sqlalchemy.orm import Session

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 视频保存目录
VIDEOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "videos")
# 确保目录存在
os.makedirs(VIDEOS_DIR, exist_ok=True)
logger.info(f"视频保存目录: {VIDEOS_DIR}")

@router.post("/simple-upload", summary="简化视频上传")
async def simple_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """简化视频上传接口（用于前端演示）"""
    
    # 创建视频记录
    video_id = str(uuid.uuid4())
    
    # 保存视频文件
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".mp4"
    file_path = os.path.join(VIDEOS_DIR, f"{video_id}{file_extension}")
    
    try:
        # 读取文件内容并保存到磁盘
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    finally:
        await file.close()
    
    video = Video(
        id=video_id,
        title=file.filename,
        description=f"上传的视频文件: {file.filename}",
        tags=["uploaded"],
        duration=0,  # 实际项目中需要解析视频时长
        play_url=f"/videos/{video_id}/play",
        cover_url=None,
        language="zh-CN",
        status="uploaded",
        video_type="long",
        author_id="demo_user"  # 演示用用户ID
    )
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # 创建长视频记录
    long_video = LongVideo(
        video_id=video_id,
        original_duration=video.duration,
        original_file_url=file_path,
        split_enabled=True
    )
    
    db.add(long_video)
    db.commit()
    db.refresh(long_video)
    
    # 在返回结果中包含 long_video_id
    response_data = VideoResponse.from_orm(video).dict()
    response_data['long_video_id'] = long_video.id
    
    return response_data