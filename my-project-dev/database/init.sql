-- 视频处理平台数据库初始化脚本
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建表结构（与SQLAlchemy模型同步）
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(500),
    bio TEXT,
    language VARCHAR(10) DEFAULT 'zh-CN',
    roles VARCHAR(50)[] DEFAULT ARRAY['learner'],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 视频表
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    author_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    tags VARCHAR(50)[],
    duration INTEGER NOT NULL,
    play_url VARCHAR(500) NOT NULL,
    cover_url VARCHAR(500),
    language VARCHAR(10) DEFAULT 'zh-CN',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    reject_reason TEXT,
    parent_video_id UUID REFERENCES long_videos(id),
    course_id UUID REFERENCES courses(id),
    segment_index INTEGER,
    video_type VARCHAR(20) DEFAULT 'short',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 长视频表
CREATE TABLE IF NOT EXISTS long_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID UNIQUE NOT NULL REFERENCES videos(id),
    original_duration INTEGER NOT NULL,
    original_file_url VARCHAR(500) NOT NULL,
    split_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 课程表
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id VARCHAR(100) UNIQUE NOT NULL,
    author_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    tags VARCHAR(50)[],
    language VARCHAR(10) DEFAULT 'zh-CN',
    cover_url VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    reject_reason TEXT,
    total_videos INTEGER DEFAULT 0,
    total_duration INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 分割任务表
CREATE TABLE IF NOT EXISTS split_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(100) UNIQUE NOT NULL,
    long_video_id UUID NOT NULL REFERENCES long_videos(id),
    user_id UUID NOT NULL REFERENCES users(id),
    split_mode VARCHAR(20) NOT NULL,
    auto_config JSONB,
    organization_mode VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress DECIMAL(5,2) DEFAULT 0.00,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- 分割片段表
CREATE TABLE IF NOT EXISTS split_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES split_tasks(id),
    segment_index INTEGER NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    thumbnail_url VARCHAR(500),
    scene_type VARCHAR(50),
    confidence DECIMAL(5,2),
    video_id UUID REFERENCES videos(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 学习记录表
CREATE TABLE IF NOT EXISTS learn_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    video_id UUID NOT NULL REFERENCES videos(id),
    last_position INTEGER DEFAULT 0,
    completed_ratio DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'not_started',
    last_watch_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id),
    user_id UUID NOT NULL REFERENCES users(id),
    parent_id UUID REFERENCES comments(id),
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 点赞表
CREATE TABLE IF NOT EXISTS likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID NOT NULL REFERENCES videos(id),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 上传任务表
CREATE TABLE IF NOT EXISTS upload_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    file_name VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'uploading',
    completed_chunks INTEGER[],
    video_type VARCHAR(20) DEFAULT 'short',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- 通知表
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    related_id VARCHAR(100),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 课程视频关联表
CREATE TABLE IF NOT EXISTS course_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id),
    video_id UUID NOT NULL REFERENCES videos(id),
    segment_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_videos_author_id ON videos(author_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_video_type ON videos(video_type);
CREATE INDEX IF NOT EXISTS idx_long_videos_video_id ON long_videos(video_id);
CREATE INDEX IF NOT EXISTS idx_courses_author_id ON courses(author_id);
CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);
CREATE INDEX IF NOT EXISTS idx_split_tasks_user_id ON split_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_split_tasks_status ON split_tasks(status);
CREATE INDEX IF NOT EXISTS idx_split_tasks_long_video_id ON split_tasks(long_video_id);
CREATE INDEX IF NOT EXISTS idx_split_segments_task_id ON split_segments(task_id);
CREATE INDEX IF NOT EXISTS idx_learn_records_user_video ON learn_records(user_id, video_id);
CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id);
CREATE INDEX IF NOT EXISTS idx_likes_video_user ON likes(video_id, user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_video_user ON favorites(video_id, user_id);
CREATE INDEX IF NOT EXISTS idx_upload_tasks_user_id ON upload_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_course_videos_course_id ON course_videos(course_id);

-- 创建默认管理员用户
INSERT INTO users (id, phone, nickname, language, roles) 
VALUES (uuid_generate_v4(), '13800138000', '系统管理员', 'zh-CN', ARRAY['admin'])
ON CONFLICT (phone) DO NOTHING;

-- 创建测试用户
INSERT INTO users (id, phone, nickname, language, roles) 
VALUES (uuid_generate_v4(), '13800138001', '测试用户', 'zh-CN', ARRAY['learner'])
ON CONFLICT (phone) DO NOTHING;