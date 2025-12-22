import uuid
import os
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from common.database.connection import get_db
from common.models import User, SplitTask, SplitSegment, Video, LongVideo
# from ..worker import celery_app  # 暂时注释掉，使用同步处理
from common.utils.auth import verify_token
from common.utils.response import success_response, error_response, not_found_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/split", tags=["split"])

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


class SegmentUpdate(BaseModel):
    """单个拆分点的更新信息"""
    segment_id: str
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    scene_type: Optional[str] = None


class UpdateSegmentsRequest(BaseModel):
    """更新拆分点请求"""
    segments: List[SegmentUpdate]


from common.utils.auth import get_current_user


@router.post("/tasks", summary="创建视频分割任务")
async def create_split_task(
    request: SplitTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建视频分割任务"""
    
    # 验证长视频是否存在
    long_video = db.query(LongVideo).filter(LongVideo.id == request.long_video_id).first()
    if not long_video:
        return not_found_response("长视频不存在")
    
    # 验证权限：确保用户只能操作自己的视频
    if long_video.video and long_video.video.author_id != current_user.id:
        return error_response("无权操作此视频", code=403)
    
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
    
    task_data = {
        "id": str(split_task.id),
        "task_id": split_task.task_id,
        "long_video_id": str(split_task.long_video_id),
        "user_id": str(split_task.user_id),
        "split_mode": split_task.split_mode,
        "auto_config": split_task.auto_config,
        "organization_mode": split_task.organization_mode,
        "status": split_task.status,
        "progress": float(split_task.progress) if split_task.progress else 0.0,
        "progress_message": split_task.progress_message or "",
        "error_message": split_task.error_message,
        "created_at": split_task.created_at.isoformat(),
        "updated_at": split_task.updated_at.isoformat() if split_task.updated_at else None,
        "completed_at": split_task.completed_at.isoformat() if split_task.completed_at else None
    }
    return success_response(data=task_data)


@router.get("/tasks", summary="获取分割任务列表")
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
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            "id": str(task.id),
            "task_id": task.task_id,
            "long_video_id": str(task.long_video_id),
            "user_id": str(task.user_id),
            "split_mode": task.split_mode,
            "auto_config": task.auto_config,
            "organization_mode": task.organization_mode,
            "status": task.status,
            "progress": float(task.progress) if task.progress else 0.0,
            "progress_message": task.progress_message or "",
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        })
    
    return success_response(data=tasks_data)


@router.get("/tasks/{task_id}", summary="获取分割任务详情")
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
        return not_found_response("任务不存在或无权访问")
    
    task_data = {
        "id": str(task.id),
        "task_id": task.task_id,
        "long_video_id": str(task.long_video_id),
        "user_id": str(task.user_id),
        "split_mode": task.split_mode,
        "auto_config": task.auto_config,
        "organization_mode": task.organization_mode,
        "status": task.status,
        "progress": float(task.progress) if task.progress is not None else 0.0,
        "progress_message": task.progress_message or "",
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }
    return success_response(data=task_data)


@router.get("/tasks/{task_id}/segments", summary="获取分割结果")
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
        return not_found_response("任务不存在或无权访问")
    
    # 获取分割片段
    segments = db.query(SplitSegment).filter(
        SplitSegment.task_id == task_id
    ).order_by(SplitSegment.segment_index).all()
    
    segments_data = []
    for segment in segments:
        segments_data.append({
            "id": str(segment.id),
            "segment_index": segment.segment_index,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "duration": segment.duration,
            "thumbnail_url": segment.thumbnail_url,
            "scene_type": segment.scene_type,
            "confidence": segment.confidence,
            "video_id": str(segment.video_id) if segment.video_id else None,
            "created_at": segment.created_at.isoformat()
        })
    
    return success_response(data=segments_data)


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
    
    # 注意：实际视频拆分已在process_split_task_sync中完成
    # 这里只是确认分割结果并创建短视频记录
    # 如果需要重新生成视频，应该调用视频拆分服务
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
            status="online",
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


@router.put("/tasks/{task_id}/segments", summary="手动调整拆分点")
async def update_split_segments(
    task_id: str,
    request: UpdateSegmentsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动调整拆分点（更新拆分片段的时间点）"""
    
    # 验证任务权限
    task = db.query(SplitTask).filter(
        SplitTask.id == task_id,
        SplitTask.user_id == current_user.id
    ).first()
    
    if not task:
        return not_found_response("任务不存在或无权访问")
    
    # 验证任务状态（只有在completed状态下才能调整）
    if task.status not in ["completed", "pending"]:
        return error_response("任务状态不允许调整拆分点", code=400)
    
    # 获取长视频信息，用于验证时间范围
    long_video = db.query(LongVideo).filter(LongVideo.id == task.long_video_id).first()
    if not long_video:
        return not_found_response("长视频不存在")
    
    max_duration = long_video.original_duration if long_video.original_duration else 999999
    
    # 更新每个拆分点
    updated_segments = []
    for segment_update in request.segments:
        # 查找拆分片段
        segment = db.query(SplitSegment).filter(
            SplitSegment.id == segment_update.segment_id,
            SplitSegment.task_id == task_id
        ).first()
        
        if not segment:
            return not_found_response(f"拆分片段 {segment_update.segment_id} 不存在")
        
        # 更新拆分点信息
        if segment_update.start_time is not None:
            if segment_update.start_time < 0 or segment_update.start_time >= max_duration:
                return error_response(f"开始时间 {segment_update.start_time} 超出有效范围", code=400)
            segment.start_time = segment_update.start_time
        
        if segment_update.end_time is not None:
            if segment_update.end_time <= 0 or segment_update.end_time > max_duration:
                return error_response(f"结束时间 {segment_update.end_time} 超出有效范围", code=400)
            segment.end_time = segment_update.end_time
            
            # 重新计算时长
            if segment.start_time is not None:
                segment.duration = segment.end_time - segment.start_time
        
        if segment_update.scene_type is not None:
            segment.scene_type = segment_update.scene_type
        
        # 标记为手动调整
        if segment.scene_type != "manual":
            segment.scene_type = "manual"
        
        updated_segments.append(segment)
    
    # 验证时间顺序（确保start_time < end_time，且片段之间不重叠）
    all_segments = db.query(SplitSegment).filter(
        SplitSegment.task_id == task_id
    ).order_by(SplitSegment.segment_index).all()
    
    for i, seg in enumerate(all_segments):
        if seg.start_time >= seg.end_time:
            return error_response(f"片段 {seg.segment_index} 的开始时间必须小于结束时间", code=400)
        if i > 0:
            prev_seg = all_segments[i - 1]
            if seg.start_time < prev_seg.end_time:
                return error_response(f"片段 {seg.segment_index} 与前一片段时间重叠", code=400)
    
    db.commit()
    
    # 返回更新后的结果
    segments = db.query(SplitSegment).filter(
        SplitSegment.task_id == task_id
    ).order_by(SplitSegment.segment_index).all()
    
    task_data = {
        "id": str(task.id),
        "task_id": task.task_id,
        "long_video_id": str(task.long_video_id),
        "user_id": str(task.user_id),
        "split_mode": task.split_mode,
        "auto_config": task.auto_config,
        "organization_mode": task.organization_mode,
        "status": task.status,
        "progress": float(task.progress) if task.progress is not None else 0.0,
        "progress_message": task.progress_message or "",
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }
    
    segments_data = []
    for segment in segments:
        segments_data.append({
            "id": str(segment.id),
            "segment_index": segment.segment_index,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "duration": segment.duration,
            "thumbnail_url": segment.thumbnail_url,
            "scene_type": segment.scene_type,
            "confidence": segment.confidence,
            "video_id": str(segment.video_id) if segment.video_id else None,
            "created_at": segment.created_at.isoformat()
        })
    
    return success_response(data={
        "task": task_data,
        "segments": segments_data
    })


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
        return not_found_response("任务不存在或无权操作")
    
    # 删除关联的分割片段
    db.query(SplitSegment).filter(SplitSegment.task_id == task_id).delete()
    
    # 删除任务
    db.delete(task)
    db.commit()
    
    return success_response(data={"message": "任务删除成功"})


# 导入视频拆分服务
from ..services.video_split_service import get_video_split_service


# 同步分割处理函数（使用服务抽象层）
def process_split_task_sync(task_id: str, db: Session):
    """处理视频分割任务（使用视频拆分服务）"""
    
    task = db.query(SplitTask).filter(SplitTask.id == task_id).first()
    if not task:
        return
    
    # 获取长视频信息
    long_video = db.query(LongVideo).filter(LongVideo.id == task.long_video_id).first()
    if not long_video:
        task.status = "failed"
        task.error_message = "长视频不存在"
        db.commit()
        return
    
    # 获取视频文件路径
    video = db.query(Video).filter(Video.id == long_video.video_id).first()
    if not video:
        task.status = "failed"
        task.error_message = "视频不存在"
        db.commit()
        return
    
    # 更新任务状态
    task.status = "processing"
    task.progress = 10.0
    task.progress_message = "开始分析视频..."
    db.commit()
    
    try:
        # 获取视频拆分服务
        split_service = get_video_split_service()
        
        # 获取视频文件路径（这里需要根据实际存储路径调整）
        video_path = video.play_url
        if not os.path.isabs(video_path):
            # 如果是相对路径，转换为绝对路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            video_path = os.path.join(base_dir, video_path.lstrip('/'))
        
        # 执行视频拆分
        task.progress = 30.0
        task.progress_message = "正在拆分视频..."
        db.commit()
        
        split_segments = split_service.split_video(
            video_path=video_path,
            split_mode=task.split_mode,
            auto_config=task.auto_config
        )
        
        # 保存分割片段
        task.progress = 70.0
        task.progress_message = "正在保存拆分结果..."
        db.commit()
        
        segments = []
        for seg_data in split_segments:
            segment = SplitSegment(
                task_id=task.id,
                segment_index=seg_data['segment_index'],
                start_time=seg_data['start_time'],
                end_time=seg_data['end_time'],
                duration=seg_data['duration'],
                thumbnail_url=seg_data.get('thumbnail_url'),
                scene_type=seg_data.get('scene_type', 'auto'),
                confidence=seg_data.get('confidence')
            )
            segments.append(segment)
            db.add(segment)
        
        # 更新任务状态
        task.status = "completed"
        task.progress = 100.0
        task.progress_message = "拆分完成"
        task.completed_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return segments
        
    except Exception as e:
        # 处理错误
        task.status = "failed"
        task.error_message = f"拆分失败: {str(e)}"
        task.progress_message = "拆分失败"
        db.commit()
        logger.error(f"视频拆分任务失败: {e}", exc_info=True)
        return []


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
        user_id="00000000-0000-0000-0000-000000000001",  # 演示用用户ID
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