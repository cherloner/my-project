import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .base import Base

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'short_video_platform')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'app_password_2025')

# 优先使用环境变量 DATABASE_URL（方便测试与不同部署）
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # 使用SQLite文件数据库进行演示
    DATABASE_URL = "sqlite:///../db.sqlite3"
    print("使用SQLite文件数据库进行演示")

# 添加连接池和超时配置
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL配置
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,  # 5分钟回收连接
        pool_size=5,
        max_overflow=10,
        connect_args={
            "connect_timeout": 10,  # 连接超时10秒
            "application_name": "short_video_api"
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
        
        # 创建演示用户
        from .models import User
        db = SessionLocal()
        try:
            # 检查demo_user是否已存在
            demo_user = db.query(User).filter(User.id == "demo_user").first()
            if not demo_user:
                # 创建演示用户
                demo_user = User(
                    id="demo_user",
                    phone="13800138000",
                    nickname="演示用户",
                    avatar_url="",
                    bio="用于前端演示的用户",
                    roles=["admin"]
                )
                db.add(demo_user)
                db.commit()
                logging.info("Demo user created successfully")
        except Exception as e:
            logging.error(f"Failed to create demo user: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise
