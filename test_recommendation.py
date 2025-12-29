#!/usr/bin/env python3
"""
测试推荐系统的脚本
"""

import sys
import os

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.content.app.services.recommendation import PopularityRecommender

# 数据库连接
DATABASE_URL = "postgresql://app_user:your_password_here@localhost:5432/short_video_platform"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_popularity_recommender():
    """测试热度推荐器"""
    db = SessionLocal()
    try:
        # 测试匿名用户的推荐
        recommender = PopularityRecommender(db, user_id=None)
        videos = recommender.recommend(limit=10)
        
        print(f"推荐视频数量: {len(videos)}")
        for i, video in enumerate(videos):
            print(f"{i+1}. {video.title} (ID: {video.id}, Status: {video.status})")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_popularity_recommender()