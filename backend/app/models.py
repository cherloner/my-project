import uuid
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, func, Boolean, DECIMAL, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

# 兼容SQLite的类型定义
# 直接使用String作为UUID类型，确保SQLite兼容
from sqlalchemy import String
UUIDType = String(36)  # UUID字符串长度
ARRAY = JSON

# 注释掉PostgreSQL类型，因为当前使用SQLite
# from sqlalchemy.dialects.postgresql import UUID as UUIDType, ARRAY


class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(20), unique=True, nullable=False)
    nickname = Column(String(50), nullable=False)
    avatar_url = Column(String(500))
    bio = Column(Text)
    language = Column(String(10), default='zh-CN')
    roles = Column(ARRAY(String(50)), default=['learner'])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String(50)))
    duration = Column(Integer, nullable=False)
    play_url = Column(String(500), nullable=False)
    cover_url = Column(String(500))
    language = Column(String(10), default='zh-CN')
    status = Column(String(20), nullable=False, default='pending')
    reject_reason = Column(Text)
    parent_video_id = Column(UUIDType, ForeignKey('long_videos.id'))
    course_id = Column(UUIDType, ForeignKey('courses.id'))
    segment_index = Column(Integer)
    video_type = Column(String(20), default='short')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    author = relationship("User", backref="videos")
    parent_long_video = relationship("LongVideo", foreign_keys=[parent_video_id])


class LearnRecord(Base):
    __tablename__ = 'learn_records'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    video_id = Column(UUIDType, ForeignKey('videos.id'), nullable=False)
    last_position = Column(Integer, default=0)
    completed_ratio = Column(DECIMAL(5, 2), default=0.00)
    status = Column(String(20), default='not_started')
    last_watch_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="learn_records")
    video = relationship("Video", backref="learn_records")


class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(UUIDType, ForeignKey('videos.id'), nullable=False)
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    parent_id = Column(UUIDType, ForeignKey('comments.id'))
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    video = relationship("Video", backref="comments")
    user = relationship("User", backref="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")


class Like(Base):
    __tablename__ = 'likes'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(UUIDType, ForeignKey('videos.id'), nullable=False)
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    video = relationship("Video", backref="likes")
    user = relationship("User", backref="likes")


class Favorite(Base):
    __tablename__ = 'favorites'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(UUIDType, ForeignKey('videos.id'), nullable=False)
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    video = relationship("Video", backref="favorites")
    user = relationship("User", backref="favorites")


class UploadTask(Base):
    __tablename__ = 'upload_tasks'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    duration = Column(Integer)
    status = Column(String(20), nullable=False, default='uploading')
    completed_chunks = Column(ARRAY(Integer))
    video_type = Column(String(20), default='short')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="upload_tasks")


class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    related_id = Column(String(100))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", backref="notifications")


class LongVideo(Base):
    __tablename__ = 'long_videos'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(UUIDType, ForeignKey('videos.id'), unique=True, nullable=False)
    original_duration = Column(Integer, nullable=False)
    original_file_url = Column(String(500), nullable=False)
    split_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    video = relationship("Video", backref="long_video", foreign_keys=[video_id])


class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String(100), unique=True, nullable=False)
    author_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(String(50)))
    language = Column(String(10), default='zh-CN')
    cover_url = Column(String(500))
    status = Column(String(20), nullable=False, default='draft')
    reject_reason = Column(Text)
    total_videos = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    author = relationship("User", backref="courses")


class CourseVideo(Base):
    __tablename__ = 'course_videos'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(UUIDType, ForeignKey('courses.id'), nullable=False)
    video_id = Column(UUIDType, ForeignKey('videos.id'), nullable=False)
    segment_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    course = relationship("Course", backref="course_videos")
    video = relationship("Video", backref="course_videos")


class SplitTask(Base):
    __tablename__ = 'split_tasks'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(100), unique=True, nullable=False)
    long_video_id = Column(UUIDType, ForeignKey('long_videos.id'), nullable=False)
    user_id = Column(UUIDType, ForeignKey('users.id'), nullable=False)
    split_mode = Column(String(20), nullable=False)
    auto_config = Column(JSON)
    organization_mode = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    progress = Column(DECIMAL(5, 2), default=0.00)
    progress_message = Column(Text, default="任务初始化中...")
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    long_video = relationship("LongVideo", backref="split_tasks")
    user = relationship("User", backref="split_tasks")


class SplitSegment(Base):
    __tablename__ = 'split_segments'
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(UUIDType, ForeignKey('split_tasks.id'), nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    thumbnail_url = Column(String(500))
    scene_type = Column(String(50))
    confidence = Column(DECIMAL(5, 2))
    video_id = Column(UUIDType, ForeignKey('videos.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    task = relationship("SplitTask", backref="split_segments")
    video = relationship("Video", backref="split_segments")