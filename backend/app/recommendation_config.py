"""
推荐系统配置管理
"""

from typing import Dict, Any


class RecommendationConfig:
    """推荐系统配置类"""
    
    # 内容推荐算法配置
    CONTENT_BASED_CONFIG = {
        "behavior_weights": {
            "like": 1.0,
            "favorite": 1.5,
            "learn": 2.0
        },
        "similarity_weights": {
            "tags": 0.4,
            "authors": 0.3,
            "languages": 0.2,
            "video_types": 0.1
        },
        "min_similarity_threshold": 0.1,
        "max_recommendations": 100
    }
    
    # 协同过滤算法配置
    COLLABORATIVE_FILTERING_CONFIG = {
        "similar_users_count": 10,
        "min_similarity_threshold": 0.1,
        "behavior_weights": {
            "liked_videos": 0.3,
            "favorited_videos": 0.4,
            "learned_videos": 0.3
        },
        "max_recommendations": 100
    }
    
    # 热度推荐算法配置
    POPULARITY_CONFIG = {
        "time_windows": {
            "day": 1,
            "week": 7,
            "month": 30,
            "all": None
        },
        "popularity_weights": {
            "likes": 1.0,
            "comments": 0.5,
            "favorites": 1.5
        },
        "decay_factor": 0.95,  # 热度衰减因子
        "max_recommendations": 100
    }
    
    # 混合推荐算法配置
    HYBRID_CONFIG = {
        "strategies": ["content", "collaborative", "popularity"],
        "weights": {
            "content": 0.6,
            "collaborative": 0.4,
            "popularity": 0.3
        },
        "switching_threshold": 10,  # 行为数量阈值
        "diversity_limits": {
            "max_videos_per_author": 3,
            "max_videos_per_tag": 5
        },
        "max_recommendations": 100
    }
    
    # 用户画像配置
    USER_PROFILE_CONFIG = {
        "profile_update_interval": 3600,  # 1小时更新一次
        "behavior_history_days": 90,  # 保留90天的行为历史
        "cold_start_threshold": 5,  # 少于5个行为视为冷启动用户
        "profile_decay_rate": 0.99  # 用户画像衰减率
    }
    
    # 推荐系统全局配置
    GLOBAL_CONFIG = {
        "cache_ttl": 3600,  # 缓存时间1小时
        "max_retries": 3,
        "timeout": 30,
        "enable_real_time_feedback": True,
        "enable_ab_testing": True,
        "default_strategy": "hybrid"
    }
    
    @classmethod
    def get_config(cls, algorithm_type: str) -> Dict[str, Any]:
        """获取指定算法的配置"""
        config_mapping = {
            "content": cls.CONTENT_BASED_CONFIG,
            "collaborative": cls.COLLABORATIVE_FILTERING_CONFIG,
            "popularity": cls.POPULARITY_CONFIG,
            "hybrid": cls.HYBRID_CONFIG,
            "user_profile": cls.USER_PROFILE_CONFIG
        }
        
        return config_mapping.get(algorithm_type, {})
    
    @classmethod
    def update_config(cls, algorithm_type: str, updates: Dict[str, Any]):
        """更新算法配置"""
        config = cls.get_config(algorithm_type)
        config.update(updates)
    
    @classmethod
    def get_global_config(cls) -> Dict[str, Any]:
        """获取全局配置"""
        return cls.GLOBAL_CONFIG.copy()


# 推荐策略配置
RECOMMENDATION_STRATEGIES = {
    "content": {
        "name": "基于内容推荐",
        "description": "根据用户历史行为和内容相似度进行推荐",
        "suitable_for": ["新用户", "有明确兴趣偏好的用户"],
        "performance_metrics": ["precision", "recall", "diversity"]
    },
    "collaborative": {
        "name": "协同过滤推荐",
        "description": "根据相似用户的行为进行推荐",
        "suitable_for": ["老用户", "有丰富行为历史的用户"],
        "performance_metrics": ["precision", "novelty", "serendipity"]
    },
    "popularity": {
        "name": "热度推荐",
        "description": "推荐当前最热门的视频",
        "suitable_for": ["所有用户", "冷启动用户"],
        "performance_metrics": ["coverage", "popularity", "recency"]
    },
    "hybrid": {
        "name": "混合推荐",
        "description": "综合多种算法进行推荐",
        "suitable_for": ["所有用户"],
        "performance_metrics": ["overall_performance", "diversity", "stability"]
    }
}


class FeatureConfig:
    """特征工程配置"""
    
    # 视频特征
    VIDEO_FEATURES = {
        "content_features": ["title", "description", "tags", "language", "video_type"],
        "statistical_features": ["like_count", "comment_count", "favorite_count", "duration"],
        "temporal_features": ["created_at", "updated_at"],
        "author_features": ["author_id", "author_popularity"]
    }
    
    # 用户特征
    USER_FEATURES = {
        "demographic_features": ["language"],
        "behavioral_features": ["likes", "favorites", "learn_records", "watch_time"],
        "preference_features": ["preferred_tags", "preferred_authors", "preferred_languages"]
    }
    
    # 交互特征
    INTERACTION_FEATURES = {
        "explicit_feedback": ["likes", "favorites", "comments"],
        "implicit_feedback": ["watch_time", "completion_rate", "repeat_views"],
        "temporal_patterns": ["time_of_day", "day_of_week", "session_duration"]
    }


class ModelConfig:
    """模型配置"""
    
    # 模型参数
    MODEL_PARAMS = {
        "content_similarity": {
            "similarity_metric": "cosine",
            "embedding_dim": 128,
            "learning_rate": 0.001
        },
        "collaborative_filtering": {
            "similarity_metric": "jaccard",
            "min_support": 5,
            "top_k": 10
        },
        "ranking_model": {
            "model_type": "lightgbm",
            "num_leaves": 31,
            "learning_rate": 0.1,
            "n_estimators": 100
        }
    }
    
    # 训练配置
    TRAINING_CONFIG = {
        "batch_size": 32,
        "epochs": 10,
        "validation_split": 0.2,
        "early_stopping_patience": 3
    }


# 配置管理器
class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.recommendation_config = RecommendationConfig()
        self.feature_config = FeatureConfig()
        self.model_config = ModelConfig()
    
    def get_full_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return {
            "recommendation": self.recommendation_config.GLOBAL_CONFIG,
            "strategies": RECOMMENDATION_STRATEGIES,
            "features": self.feature_config.VIDEO_FEATURES,
            "models": self.model_config.MODEL_PARAMS
        }
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        # 检查权重总和
        hybrid_weights = self.recommendation_config.HYBRID_CONFIG["weights"]
        weight_sum = sum(hybrid_weights.values())
        
        if abs(weight_sum - 1.0) > 0.01:  # 允许1%的误差
            return False
        
        # 检查其他配置约束
        # 这里可以添加更多的验证逻辑
        
        return True