import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models import User, SplitTask, SplitSegment, Video, LongVideo
# from ..worker import celery_app  # 暂时注释掉，使用同步处理
from .auth import verify_token

router = APIRouter(prefix="/split", tags=["split"])

security = HTTPBearer()


class SplitTaskRequest(BaseModel):
    long_video_id: str
    split_mode: str  # auto, manual, scene
    auto_config: Optional[Dict[str, Any]] = None
    organization_mode: str  # course, standalone


class SplitTaskResponse(BaseModel):
    id: str
    task_id: str
    long_video_id: str
    user_id: str
    split_mode: str
    auto_config: Optional[Dict[str, Any]]
    organization_mode: str
    status: str
    progress: float
    progress_message: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]  # 设为可选，避免验证失败
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SplitSegmentResponse(BaseModel):
    id: str
    segment_index: int
    start_time: int
    end_time: int
    duration: int
    thumbnail_url: Optional[str]
    scene_type: Optional[str]
    confidence: Optional[float]
    video_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SplitResultResponse(BaseModel):
    task: SplitTaskResponse
    segments: List[SplitSegmentResponse]


def get_current_user(
    db: Session = Depends(get_db)
):
    """获取当前用户 - 演示模式下默认使用demo_user"""
    # 演示模式：默认使用demo_user，完全跳过认证
    user = db.query(User).filter(User.id == "demo_user").first()
    if user is None:
        raise HTTPException(status_code=404, detail="演示用户不存在")
    return user


@router.post("/tasks", response_model=SplitTaskResponse, summary="创建视频分割任务")
async def create_split_task(
    request: SplitTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建视频分割任务"""
    
    # 验证长视频是否存在
    long_video = db.query(LongVideo).filter(LongVideo.id == request.long_video_id).first()
    if not long_video:
        raise HTTPException(status_code=404, detail="长视频不存在")
    
    # 演示模式：跳过权限检查
    
    # 生成任务ID
    task_id = f"split_{uuid.uuid4().hex[:8]}"
    
    # 创建分割任务
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    split_task = SplitTask(
        task_id=task_id,
        long_video_id=long_video.id,
        user_id=current_user.id,
        split_mode=request.split_mode,
        auto_config=request.auto_config,
        organization_mode=request.organization_mode,
        status="pending",
        progress=0.0,
        created_at=now,
        updated_at=now
    )
    
    db.add(split_task)
    db.commit()
    db.refresh(split_task)
    
    # 触发异步任务处理
    try:
        # 获取长视频信息
        long_video = db.query(LongVideo).filter(LongVideo.id == request.long_video_id).first()
        if long_video:
            # 使用同步处理替代Celery任务（演示模式）
            print(f"准备处理切分任务: task_id={split_task.task_id}, long_video_id={str(long_video.id)}")
            
            # 直接调用同步处理函数
            process_split_task_sync(str(split_task.id), db)
            
            # 立即更新任务状态为processing，避免前端显示0%卡住
            split_task.status = "processing"
            split_task.progress = 5.0  # 初始进度
            db.commit()
    except Exception as e:
        # 记录错误并更新任务状态为失败
        print(f"触发异步任务失败: {e}")
        split_task.status = "failed"
        split_task.error_message = f"任务启动失败: {str(e)}"
        db.commit()
        import traceback
        traceback.print_exc()
    
    return SplitTaskResponse.from_orm(split_task)


@router.get("/tasks", response_model=List[SplitTaskResponse], summary="获取分割任务列表")
async def get_split_tasks(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的分割任务列表"""
    
    query = db.query(SplitTask).filter(SplitTask.user_id == current_user.id)
    
    if status:
        query = query.filter(SplitTask.status == status)
    
    tasks = query.order_by(SplitTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return [SplitTaskResponse.from_orm(task) for task in tasks]


@router.get("/tasks/{task_id}", response_model=SplitTaskResponse, summary="获取分割任务详情")
async def get_split_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分割任务详情"""
    
    task = db.query(SplitTask).filter(
        SplitTask.id == task_id,
        SplitTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    
    return SplitTaskResponse.from_orm(task)


@router.get("/tasks/{task_id}/segments", response_model=List[SplitSegmentResponse], summary="获取分割结果")
async def get_split_segments(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分割任务的结果片段"""
    
    # 验证任务权限
    task = db.query(SplitTask).filter(
        SplitTask.id == task_id,
        SplitTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    
    # 获取分割片段
    segments = db.query(SplitSegment).filter(
        SplitSegment.task_id == task_id
    ).order_by(SplitSegment.segment_index).all()
    
    return [SplitSegmentResponse.from_orm(segment) for segment in segments]


@router.get("/tasks/{task_id}/result", response_model=SplitResultResponse, summary="获取完整分割结果")
async def get_split_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取完整的分割结果（包含任务和片段）"""
    
    # 验证任务权限
    task = db.query(SplitTask).filter(
        SplitTask.id == task_id,
        SplitTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    
    # 获取分割片段
    segments = db.query(SplitSegment).filter(
        SplitSegment.task_id == task_id
    ).order_by(SplitSegment.segment_index).all()
    
    return SplitResultResponse(
        task=SplitTaskResponse.from_orm(task),
        segments=[SplitSegmentResponse.from_orm(segment) for segment in segments]
    )


@router.post("/tasks/{task_id}/confirm", response_model=SplitResultResponse, summary="确认分割结果")
async def confirm_split_result(
    task_id: str,
    segment_ids: List[str],  # 用户确认的片段ID列表
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认分割结果并生成短视频"""
    
    # 验证任务权限
    task = db.query(SplitTask).filter(
        SplitTask.id == task_id,
        SplitTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权访问")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    # 获取长视频信息
    long_video = db.query(LongVideo).filter(LongVideo.id == task.long_video_id).first()
    if not long_video:
        raise HTTPException(status_code=404, detail="长视频不存在")
    
    # 获取用户确认的片段
    segments = db.query(SplitSegment).filter(
        SplitSegment.task_id == task_id,
        SplitSegment.id.in_(segment_ids)
    ).order_by(SplitSegment.segment_index).all()
    
    if not segments:
        raise HTTPException(status_code=400, detail="未选择任何片段")
    
    # TODO: 实际项目中这里应该调用视频处理服务
    # 根据分割片段生成短视频
    
    # 模拟生成短视频
    for i, segment in enumerate(segments):
        # 创建短视频记录
        video = Video(
            author_id=current_user.id,
            title=f"{task.task_id}_segment_{segment.segment_index}",
            description=f"从长视频分割出的片段 {segment.segment_index}",
            duration=segment.duration,
            play_url=f"/videos/split/{task_id}/segment_{segment.segment_index}",
            cover_url=segment.thumbnail_url,
            language="zh-CN",
            status="approved",
            video_type="short",
            parent_video_id=long_video.video_id
        )
        
        db.add(video)
        db.flush()  # 获取video.id
        
        # 更新片段关联的短视频ID
        segment.video_id = video.id
    
    # 更新任务状态
    task.status = "confirmed"
    
    db.commit()
    
    # 返回确认后的结果
    segments = db.query(SplitSegment).filter(
        SplitSegment.task_id == task_id
    ).order_by(SplitSegment.segment_index).all()
    
    return SplitResultResponse(
        task=SplitTaskResponse.from_orm(task),
        segments=[SplitSegmentResponse.from_orm(segment) for segment in segments]
    )


@router.delete("/tasks/{task_id}", summary="删除分割任务")
async def delete_split_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除分割任务"""
    
    task = db.query(SplitTask).filter(
        SplitTask.id == task_id,
        SplitTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权操作")
    
    # 删除关联的分割片段
    db.query(SplitSegment).filter(SplitSegment.task_id == task_id).delete()
    
    # 删除任务
    db.delete(task)
    db.commit()
    
    return {"message": "任务删除成功"}


# 同步分割处理函数（演示模式）
def process_split_task_sync(task_id: str, db: Session):
    """处理视频分割任务（模拟实现）"""
    
    task = db.query(SplitTask).filter(SplitTask.id == task_id).first()
    if not task:
        return
    
    # 模拟处理过程
    task.status = "processing"
    task.progress = 10.0
    db.commit()
    
    # 模拟分析视频并生成分割点
    # 这里应该调用实际的视频分析算法
    
    # 模拟生成5个分割片段
    segments = []
    for i in range(5):
        start_time = i * 60  # 每60秒一个片段
        end_time = (i + 1) * 60
        duration = 60
        
        segment = SplitSegment(
            task_id=task.id,
            segment_index=i,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            thumbnail_url=f"/thumbnails/{task_id}/segment_{i}.jpg",
            scene_type="general",
            confidence=0.85
        )
        segments.append(segment)
    
    # 保存分割片段
    for segment in segments:
        db.add(segment)
    
    # 更新任务状态
    task.status = "completed"
    task.progress = 100.0
    task.completed_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return segments


# 简化分割接口 - 用于前端演示
@router.post("/simple-split", summary="简化视频分割")
async def simple_split(
    video_id: str,
    threshold: float = 0.15,
    db: Session = Depends(get_db)
):
    """简化视频分割接口（用于前端演示）"""
    
    # 创建分割任务
    task_id = f"split_{uuid.uuid4().hex[:8]}"
    
    # 创建长视频记录（如果不存在）
    long_video = db.query(LongVideo).filter(LongVideo.video_id == video_id).first()
    if not long_video:
        long_video = LongVideo(
            video_id=video_id,
            original_duration=300,  # 假设5分钟视频
            original_file_url=f"/videos/{video_id}/original"
        )
        db.add(long_video)
        db.commit()
        db.refresh(long_video)
    
    # 创建分割任务
    split_task = SplitTask(
        task_id=task_id,
        long_video_id=long_video.id,
        user_id="demo_user",  # 演示用用户ID
        split_mode="auto",
        auto_config={"threshold": threshold},
        organization_mode="standalone",
        status="completed",  # 直接标记为完成
        progress=100.0,
        completed_at=datetime.now(timezone.utc)
    )
    
    db.add(split_task)
    db.commit()
    db.refresh(split_task)
    
    # 模拟生成分割片段
    segments = []
    for i in range(5):
        start_time = i * 60  # 每60秒一个片段
        end_time = (i + 1) * 60
        duration = 60
        
        segment = SplitSegment(
            task_id=split_task.id,
            segment_index=i,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            thumbnail_url=f"/thumbnails/{task_id}/segment_{i}.jpg",
            scene_type="general",
            confidence=0.85
        )
        segments.append(segment)
    
    # 保存分割片段
    for segment in segments:
        db.add(segment)
    
    db.commit()
    
    return {
        "task_id": split_task.task_id,
        "segments": [
            {
                "id": str(segment.id),
                "segment_index": segment.segment_index,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.duration
            }
            for segment in segments
        ],
        "message": "分割完成"
    }