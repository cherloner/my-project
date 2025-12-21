import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, and_
from pydantic import BaseModel
import math

from ..database import get_db
from ..models import User, Video, Like, Favorite, Comment, LearnRecord
from ..recommendation import (
    ContentBasedRecommender, CollaborativeFilteringRecommender,
    HybridRecommender, PopularityRecommender, RecommendationService
)
from .auth import verify_token

router = APIRouter(prefix="/feed", tags=["feed"])

security = HTTPBearer()


class VideoFeedResponse(BaseModel):
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
    author_nickname: str
    author_avatar: Optional[str]
    like_count: int
    comment_count: int
    favorite_count: int
    is_liked: bool = False
    is_favorited: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedResponse(BaseModel):
    videos: List[VideoFeedResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    next_cursor: Optional[str] = None


class SearchResponse(BaseModel):
    videos: List[VideoFeedResponse]
    total: int
    query: str
    search_type: str


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





@router.get("/recommend", response_model=FeedResponse, summary="智能推荐视频流")
async def get_recommend_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    strategy: str = Query("hybrid", regex="^(hybrid|content|collaborative|popularity)$", description="推荐策略"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取智能推荐视频流"""
    
    # 初始化推荐服务
    recommendation_service = RecommendationService(db)
    
    # 获取推荐视频
    recommended_videos = recommendation_service.get_recommendations(
        user_id=str(current_user.id),
        strategy=strategy,
        limit=page_size * 5  # 获取更多用于分页
    )
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 分页处理
    total = len(recommended_videos)
    videos = recommended_videos[offset:offset + page_size]
    
    # 获取用户互动信息
    video_ids = [str(video.id) for video in videos]
    
    # 获取点赞信息
    user_likes = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id.in_(video_ids)
    ).all()
    liked_video_ids = {str(like.video_id) for like in user_likes}
    
    # 获取收藏信息
    user_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id.in_(video_ids)
    ).all()
    favorited_video_ids = {str(favorite.video_id) for favorite in user_favorites}
    
    # 构建响应数据
    feed_videos = []
    for video in videos:
        # 获取统计信息
        like_count = db.query(Like).filter(Like.video_id == video.id).count()
        comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
        favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
        
        feed_videos.append(VideoFeedResponse(
            id=str(video.id),
            title=video.title,
            description=video.description,
            tags=video.tags,
            duration=video.duration,
            play_url=video.play_url,
            cover_url=video.cover_url,
            language=video.language,
            status=video.status,
            video_type=video.video_type,
            author_id=str(video.author_id),
            author_nickname=video.author.nickname,
            author_avatar=video.author.avatar_url,
            like_count=like_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            is_liked=str(video.id) in liked_video_ids,
            is_favorited=str(video.id) in favorited_video_ids,
            created_at=video.created_at
        ))
    
    # 计算是否有下一页
    has_next = offset + len(videos) < total
    next_cursor = str(uuid.uuid4()) if has_next else None
    
    return FeedResponse(
        videos=feed_videos,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        next_cursor=next_cursor
    )


@router.get("/diverse", response_model=FeedResponse, summary="多样化推荐")
async def get_diverse_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取多样化推荐视频流（多种算法混合）"""
    
    # 初始化推荐服务
    recommendation_service = RecommendationService(db)
    
    # 获取多样化推荐
    recommended_videos = recommendation_service.get_diverse_recommendations(
        user_id=str(current_user.id),
        limit=page_size * 5
    )
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 分页处理
    total = len(recommended_videos)
    videos = recommended_videos[offset:offset + page_size]
    
    # 获取用户互动信息
    video_ids = [str(video.id) for video in videos]
    
    # 获取点赞信息
    user_likes = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id.in_(video_ids)
    ).all()
    liked_video_ids = {str(like.video_id) for like in user_likes}
    
    # 获取收藏信息
    user_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id.in_(video_ids)
    ).all()
    favorited_video_ids = {str(favorite.video_id) for favorite in user_favorites}
    
    # 构建响应数据
    feed_videos = []
    for video in videos:
        # 获取统计信息
        like_count = db.query(Like).filter(Like.video_id == video.id).count()
        comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
        favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
        
        feed_videos.append(VideoFeedResponse(
            id=str(video.id),
            title=video.title,
            description=video.description,
            tags=video.tags,
            duration=video.duration,
            play_url=video.play_url,
            cover_url=video.cover_url,
            language=video.language,
            status=video.status,
            video_type=video.video_type,
            author_id=str(video.author_id),
            author_nickname=video.author.nickname,
            author_avatar=video.author.avatar_url,
            like_count=like_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            is_liked=str(video.id) in liked_video_ids,
            is_favorited=str(video.id) in favorited_video_ids,
            created_at=video.created_at
        ))
    
    # 计算是否有下一页
    has_next = offset + len(videos) < total
    next_cursor = str(uuid.uuid4()) if has_next else None
    
    return FeedResponse(
        videos=feed_videos,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        next_cursor=next_cursor
    )


@router.get("/personalized", response_model=FeedResponse, summary="个性化推荐")
async def get_personalized_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    tags: Optional[str] = Query(None, description="指定标签，多个用逗号分隔"),
    language: Optional[str] = Query(None, description="指定语言"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取个性化推荐视频流（可指定偏好）"""
    
    # 初始化推荐服务
    recommendation_service = RecommendationService(db)
    
    # 获取基础推荐
    recommended_videos = recommendation_service.get_recommendations(
        user_id=str(current_user.id),
        strategy="content",  # 使用内容推荐进行个性化
        limit=page_size * 5
    )
    
    # 如果指定了标签，进行过滤
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        recommended_videos = [
            video for video in recommended_videos 
            if video.tags and any(tag in video.tags for tag in tag_list)
        ]
    
    # 如果指定了语言，进行过滤
    if language:
        recommended_videos = [
            video for video in recommended_videos 
            if video.language == language
        ]
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 分页处理
    total = len(recommended_videos)
    videos = recommended_videos[offset:offset + page_size]
    
    # 获取用户互动信息
    video_ids = [str(video.id) for video in videos]
    
    # 获取点赞信息
    user_likes = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id.in_(video_ids)
    ).all()
    liked_video_ids = {str(like.video_id) for like in user_likes}
    
    # 获取收藏信息
    user_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id.in_(video_ids)
    ).all()
    favorited_video_ids = {str(favorite.video_id) for favorite in user_favorites}
    
    # 构建响应数据
    feed_videos = []
    for video in videos:
        # 获取统计信息
        like_count = db.query(Like).filter(Like.video_id == video.id).count()
        comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
        favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
        
        feed_videos.append(VideoFeedResponse(
            id=str(video.id),
            title=video.title,
            description=video.description,
            tags=video.tags,
            duration=video.duration,
            play_url=video.play_url,
            cover_url=video.cover_url,
            language=video.language,
            status=video.status,
            video_type=video.video_type,
            author_id=str(video.author_id),
            author_nickname=video.author.nickname,
            author_avatar=video.author.avatar_url,
            like_count=like_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            is_liked=str(video.id) in liked_video_ids,
            is_favorited=str(video.id) in favorited_video_ids,
            created_at=video.created_at
        ))
    
    # 计算是否有下一页
    has_next = offset + len(videos) < total
    next_cursor = str(uuid.uuid4()) if has_next else None
    
    return FeedResponse(
        videos=feed_videos,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        next_cursor=next_cursor
    )


class FeedbackRequest(BaseModel):
    video_id: str
    action_type: str  # like, favorite, watch, skip
    feedback_value: Optional[float] = 1.0


@router.post("/feedback", summary="推荐反馈")
async def submit_recommendation_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交推荐反馈（用于优化推荐算法）"""
    
    # 验证视频存在
    video = db.query(Video).filter(Video.id == feedback.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 这里可以记录用户的反馈行为
    # 在实际应用中，可以结合缓存和异步处理来更新推荐模型
    
    # 示例：记录用户对推荐视频的反馈
    # 可以存储在专门的推荐反馈表中，用于模型训练
    
    return {"message": "反馈已接收，将用于优化推荐效果"}


@router.get("/following", response_model=FeedResponse, summary="关注用户视频流")
async def get_following_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取关注用户的视频流"""
    
    # TODO: 实现关注关系逻辑
    # 目前先返回推荐视频流
    return await get_recommend_feed(page, page_size, current_user, db)


@router.get("/hot", response_model=FeedResponse, summary="热门视频")
async def get_hot_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取热门视频（按点赞数排序）"""
    
    offset = (page - 1) * page_size
    
    # 查询热门视频（按点赞数排序）
    query = db.query(
        Video,
        func.count(Like.id).label('like_count')
    ).outerjoin(
        Like, Video.id == Like.video_id
    ).filter(
        Video.status == "approved",
        Video.video_type == "short"
    ).group_by(Video.id).order_by(desc('like_count'))
    
    # 获取总数
    total = query.count()
    
    # 获取视频列表
    results = query.offset(offset).limit(page_size).all()
    videos = [result[0] for result in results]
    
    # 获取用户互动信息
    video_ids = [str(video.id) for video in videos]
    
    user_likes = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id.in_(video_ids)
    ).all()
    liked_video_ids = {str(like.video_id) for like in user_likes}
    
    user_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id.in_(video_ids)
    ).all()
    favorited_video_ids = {str(favorite.video_id) for favorite in user_favorites}
    
    # 构建响应数据
    feed_videos = []
    for video in videos:
        like_count = db.query(Like).filter(Like.video_id == video.id).count()
        comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
        favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
        
        feed_videos.append(VideoFeedResponse(
            id=str(video.id),
            title=video.title,
            description=video.description,
            tags=video.tags,
            duration=video.duration,
            play_url=video.play_url,
            cover_url=video.cover_url,
            language=video.language,
            status=video.status,
            video_type=video.video_type,
            author_id=str(video.author_id),
            author_nickname=video.author.nickname,
            author_avatar=video.author.avatar_url,
            like_count=like_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            is_liked=str(video.id) in liked_video_ids,
            is_favorited=str(video.id) in favorited_video_ids,
            created_at=video.created_at
        ))
    
    has_next = offset + len(videos) < total
    next_cursor = str(uuid.uuid4()) if has_next else None
    
    return FeedResponse(
        videos=feed_videos,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        next_cursor=next_cursor
    )


@router.get("/diverse", response_model=FeedResponse, summary="多样化推荐")
async def get_diverse_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取多样化推荐视频流（多种算法混合）"""
    
    # 初始化推荐服务
    recommendation_service = RecommendationService(db)
    
    # 获取多样化推荐
    recommended_videos = recommendation_service.get_diverse_recommendations(
        user_id=str(current_user.id),
        limit=page_size * 5
    )
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 分页处理
    total = len(recommended_videos)
    videos = recommended_videos[offset:offset + page_size]
    
    # 获取用户互动信息
    video_ids = [str(video.id) for video in videos]
    
    # 获取点赞信息
    user_likes = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id.in_(video_ids)
    ).all()
    liked_video_ids = {str(like.video_id) for like in user_likes}
    
    # 获取收藏信息
    user_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id.in_(video_ids)
    ).all()
    favorited_video_ids = {str(favorite.video_id) for favorite in user_favorites}
    
    # 构建响应数据
    feed_videos = []
    for video in videos:
        # 获取统计信息
        like_count = db.query(Like).filter(Like.video_id == video.id).count()
        comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
        favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
        
        feed_videos.append(VideoFeedResponse(
            id=str(video.id),
            title=video.title,
            description=video.description,
            tags=video.tags,
            duration=video.duration,
            play_url=video.play_url,
            cover_url=video.cover_url,
            language=video.language,
            status=video.status,
            video_type=video.video_type,
            author_id=str(video.author_id),
            author_nickname=video.author.nickname,
            author_avatar=video.author.avatar_url,
            like_count=like_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            is_liked=str(video.id) in liked_video_ids,
            is_favorited=str(video.id) in favorited_video_ids,
            created_at=video.created_at
        ))
    
    # 计算是否有下一页
    has_next = offset + len(videos) < total
    next_cursor = str(uuid.uuid4()) if has_next else None
    
    return FeedResponse(
        videos=feed_videos,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        next_cursor=next_cursor
    )


@router.get("/personalized", response_model=FeedResponse, summary="个性化推荐")
async def get_personalized_feed(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    tags: Optional[str] = Query(None, description="指定标签，多个用逗号分隔"),
    language: Optional[str] = Query(None, description="指定语言"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取个性化推荐视频流（可指定偏好）"""
    
    # 初始化推荐服务
    recommendation_service = RecommendationService(db)
    
    # 获取基础推荐
    recommended_videos = recommendation_service.get_recommendations(
        user_id=str(current_user.id),
        strategy="content",  # 使用内容推荐进行个性化
        limit=page_size * 5
    )
    
    # 如果指定了标签，进行过滤
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        recommended_videos = [
            video for video in recommended_videos 
            if video.tags and any(tag in video.tags for tag in tag_list)
        ]
    
    # 如果指定了语言，进行过滤
    if language:
        recommended_videos = [
            video for video in recommended_videos 
            if video.language == language
        ]
    
    # 计算偏移量
    offset = (page - 1) * page_size
    
    # 分页处理
    total = len(recommended_videos)
    videos = recommended_videos[offset:offset + page_size]
    
    # 获取用户互动信息
    video_ids = [str(video.id) for video in videos]
    
    # 获取点赞信息
    user_likes = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id.in_(video_ids)
    ).all()
    liked_video_ids = {str(like.video_id) for like in user_likes}
    
    # 获取收藏信息
    user_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id.in_(video_ids)
    ).all()
    favorited_video_ids = {str(favorite.video_id) for favorite in user_favorites}
    
    # 构建响应数据
    feed_videos = []
    for video in videos:
        # 获取统计信息
        like_count = db.query(Like).filter(Like.video_id == video.id).count()
        comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
        favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
        
        feed_videos.append(VideoFeedResponse(
            id=str(video.id),
            title=video.title,
            description=video.description,
            tags=video.tags,
            duration=video.duration,
            play_url=video.play_url,
            cover_url=video.cover_url,
            language=video.language,
            status=video.status,
            video_type=video.video_type,
            author_id=str(video.author_id),
            author_nickname=video.author.nickname,
            author_avatar=video.author.avatar_url,
            like_count=like_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            is_liked=str(video.id) in liked_video_ids,
            is_favorited=str(video.id) in favorited_video_ids,
            created_at=video.created_at
        ))
    
    # 计算是否有下一页
    has_next = offset + len(videos) < total
    next_cursor = str(uuid.uuid4()) if has_next else None
    
    return FeedResponse(
        videos=feed_videos,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        next_cursor=next_cursor
    )


class FeedbackRequest(BaseModel):
    video_id: str
    action_type: str  # like, favorite, watch, skip
    feedback_value: Optional[float] = 1.0


@router.post("/feedback", summary="推荐反馈")
async def submit_recommendation_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交推荐反馈（用于优化推荐算法）"""
    
    # 验证视频存在
    video = db.query(Video).filter(Video.id == feedback.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 这里可以记录用户的反馈行为
    # 在实际应用中，可以结合缓存和异步处理来更新推荐模型
    
    # 示例：记录用户对推荐视频的反馈
    # 可以存储在专门的推荐反馈表中，用于模型训练
    
    return {"message": "反馈已接收，将用于优化推荐效果"}


@router.get("/search", response_model=SearchResponse, summary="搜索视频")
async def search_videos(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    search_type: str = Query("all", regex="^(all|title|tag|author)$", description="搜索类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索视频"""
    
    offset = (page - 1) * page_size
    
    # 构建搜索查询
    query = db.query(Video).filter(
        Video.status == "approved",
        Video.video_type == "short"
    )
    
    # 根据搜索类型添加搜索条件
    search_conditions = []
    if search_type in ["all", "title"]:
        search_conditions.append(Video.title.ilike(f"%{q}%"))
    
    if search_type in ["all", "tag"] and Video.tags is not None:
        # 对于数组字段的搜索
        search_conditions.append(
            Video.tags.any(q)
        )
    
    if search_type in ["all", "author"]:
        search_conditions.append(User.nickname.ilike(f"%{q}%"))
        query = query.join(User, Video.author_id == User.id)
    
    if search_conditions:
        query = query.filter(or_(*search_conditions))
    
    # 获取总数
    total = query.count()
    
    # 获取搜索结果
    videos = query.order_by(desc(Video.created_at)).offset(offset).limit(page_size).all()
    
    # 获取用户互动信息
    video_ids = [str(video.id) for video in videos]
    
    user_likes = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id.in_(video_ids)
    ).all()
    liked_video_ids = {str(like.video_id) for like in user_likes}
    
    user_favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id.in_(video_ids)
    ).all()
    favorited_video_ids = {str(favorite.video_id) for favorite in user_favorites}
    
    # 构建响应数据
    search_videos = []
    for video in videos:
        like_count = db.query(Like).filter(Like.video_id == video.id).count()
        comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
        favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
        
        search_videos.append(VideoFeedResponse(
            id=str(video.id),
            title=video.title,
            description=video.description,
            tags=video.tags,
            duration=video.duration,
            play_url=video.play_url,
            cover_url=video.cover_url,
            language=video.language,
            status=video.status,
            video_type=video.video_type,
            author_id=str(video.author_id),
            author_nickname=video.author.nickname,
            author_avatar=video.author.avatar_url,
            like_count=like_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            is_liked=str(video.id) in liked_video_ids,
            is_favorited=str(video.id) in favorited_video_ids,
            created_at=video.created_at
        ))
    
    return SearchResponse(
        videos=search_videos,
        total=total,
        query=q,
        search_type=search_type
    )


@router.get("/video/{video_id}", response_model=VideoFeedResponse, summary="获取视频详情")
async def get_video_detail(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取视频详情"""
    
    # 查询视频
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.status == "approved"
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在或已被删除")
    
    # 获取统计信息
    like_count = db.query(Like).filter(Like.video_id == video.id).count()
    comment_count = db.query(Comment).filter(Comment.video_id == video.id).count()
    favorite_count = db.query(Favorite).filter(Favorite.video_id == video.id).count()
    
    # 获取用户互动状态
    is_liked = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.video_id == video.id
    ).first() is not None
    
    is_favorited = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.video_id == video.id
    ).first() is not None
    
    # 创建学习记录（如果不存在）
    learn_record = db.query(LearnRecord).filter(
        LearnRecord.user_id == current_user.id,
        LearnRecord.video_id == video.id
    ).first()
    
    if not learn_record:
        learn_record = LearnRecord(
            user_id=current_user.id,
            video_id=video.id,
            status="not_started"
        )
        db.add(learn_record)
        db.commit()
    
    return VideoFeedResponse(
        id=str(video.id),
        title=video.title,
        description=video.description,
        tags=video.tags,
        duration=video.duration,
        play_url=video.play_url,
        cover_url=video.cover_url,
        language=video.language,
        status=video.status,
        video_type=video.video_type,
        author_id=str(video.author_id),
        author_nickname=video.author.nickname,
        author_avatar=video.author.avatar_url,
        like_count=like_count,
        comment_count=comment_count,
        favorite_count=favorite_count,
        is_liked=is_liked,
        is_favorited=is_favorited,
        created_at=video.created_at
    )