"""
视频分割服务适配器
将现有的split.py功能集成到FastAPI系统中
"""
import os
import sys
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(project_root)

try:
    from split import VideoSplitter
    print(f"成功导入VideoSplitter类 from {project_root}/split.py")
except ImportError as e:
    print(f"导入VideoSplitter类失败: {e}")
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path}")
    # 导入失败时抛出异常，而不是使用模拟类
    raise


class VideoSplitService:
    """视频分割服务"""
    
    def __init__(self, base_video_path: str = "videos", base_output_path: str = "output_splited_videos"):
        self.base_video_path = base_video_path
        self.base_output_path = base_output_path
        
        # 确保目录存在
        os.makedirs(self.base_video_path, exist_ok=True)
        os.makedirs(self.base_output_path, exist_ok=True)
    
    def split_video(self, video_filename: str, knowledge_filename: str, 
                   task_id: str, split_mode: str = "auto", 
                   auto_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        分割视频
        
        Args:
            video_filename: 视频文件名
            knowledge_filename: 知识点文件名
            task_id: 任务ID
            split_mode: 分割模式
            auto_config: 自动配置参数
            
        Returns:
            分割结果列表
        """
        
        # 构建完整路径
        video_path = os.path.join(self.base_video_path, video_filename)
        knowledge_path = os.path.join("output", knowledge_filename)
        
        # 创建任务特定的输出目录
        task_output_dir = os.path.join(self.base_output_path, task_id)
        os.makedirs(task_output_dir, exist_ok=True)
        
        # 检查文件是否存在
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        if not os.path.exists(knowledge_path):
            raise FileNotFoundError(f"知识点文件不存在: {knowledge_path}")
        
        try:
            # 创建视频分割器实例
            splitter = VideoSplitter(
                video_path=video_path,
                knowledge_file=knowledge_path,
                output_dir=task_output_dir
            )
            
            # 执行分割
            segments = splitter.run_noninteractive(method='copy', overwrite=True)
            
            # 格式化分割结果
            formatted_segments = []
            for segment in segments:
                knowledge_point = segment.get('knowledge_point', {})
                
                formatted_segment = {
                    'segment_index': knowledge_point.get('index', 0),
                    'start_time': knowledge_point.get('start_time', 0),
                    'end_time': knowledge_point.get('end_time', 0),
                    'duration': knowledge_point.get('duration', 0),
                    'thumbnail_url': segment.get('thumbnail'),
                    'scene_type': knowledge_point.get('scene_type'),
                    'confidence': knowledge_point.get('confidence'),
                    'video_file': segment.get('output_file'),
                    'created_at': datetime.now()
                }
                
                formatted_segments.append(formatted_segment)
            
            return formatted_segments
            
        except Exception as e:
            raise RuntimeError(f"视频分割失败: {str(e)}")
    
    def generate_knowledge_file(self, video_id: str, content: str) -> str:
        """
        生成知识点文件
        
        Args:
            video_id: 视频ID
            content: 知识点内容
            
        Returns:
            生成的文件名
        """
        filename = f"knowledge_points_{video_id}.txt"
        filepath = os.path.join("output", filename)
        
        # 确保目录存在
        os.makedirs("output", exist_ok=True)
        
        # 写入知识点文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename


# 创建全局实例
video_split_service = VideoSplitService()