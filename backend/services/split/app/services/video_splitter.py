"""
视频切分工具 - 基于时间戳使用ffmpeg切分视频
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class VideoSplitter:
    """使用ffmpeg按时间戳切分视频"""
    
    def split_segment(
        self,
        video_path: str,
        start_time: int,
        end_time: int,
        output_dir: str,
        segment_index: int,
        generate_thumbnail: bool = True
    ) -> Tuple[str, Optional[str]]:
        """切分单个视频片段
        
        Args:
            video_path: 原视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_dir: 输出目录
            segment_index: 片段索引
            generate_thumbnail: 是否生成缩略图
            
        Returns:
            元组 (视频文件路径, 缩略图路径)
        """
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        output_file = output_path / f"segment_{segment_index:03d}.mp4"
        
        # 计算时长
        duration = end_time - start_time
        
        # 使用ffmpeg切分视频
        # -ss: 开始时间  -t: 持续时间  -c copy: 直接复制流（速度快）
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',  # 直接复制流，不重新编码
            '-avoid_negative_ts', '1',  # 避免负时间戳
            '-y',  # 覆盖已存在的文件
            str(output_file)
        ]
        
        logger.info(f"执行ffmpeg切分: segment_{segment_index} ({start_time}s - {end_time}s)")
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"ffmpeg切分失败: {result.stderr}")
                raise RuntimeError(f"视频切分失败: {result.stderr}")
            
            logger.info(f"切分完成: {output_file}")
            
            # 生成缩略图
            thumbnail_path = None
            if generate_thumbnail:
                thumbnail_path = self._generate_thumbnail(
                    video_path=video_path,
                    timestamp=start_time + duration / 2,  # 取中间帧
                    output_dir=output_dir,
                    segment_index=segment_index
                )
            
            return str(output_file), thumbnail_path
            
        except subprocess.TimeoutExpired:
            logger.error(f"ffmpeg切分超时: segment_{segment_index}")
            raise RuntimeError(f"视频切分超时")
        except Exception as e:
            logger.error(f"ffmpeg切分异常: {e}")
            raise
    
    def _generate_thumbnail(
        self,
        video_path: str,
        timestamp: float,
        output_dir: str,
        segment_index: int
    ) -> Optional[str]:
        """生成视频缩略图
        
        Args:
            video_path: 视频文件路径
            timestamp: 截图时间戳（秒）
            output_dir: 输出目录
            segment_index: 片段索引
            
        Returns:
            缩略图文件路径，失败返回None
        """
        try:
            output_path = Path(output_dir)
            thumbnail_file = output_path / f"segment_{segment_index:03d}_thumb.jpg"
            
            # 使用ffmpeg提取帧
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',  # 只提取一帧
                '-q:v', '2',  # JPEG质量（1-31，2为高质量）
                '-vf', 'scale=320:-1',  # 宽度320px，高度自适应
                '-y',
                str(thumbnail_file)
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and thumbnail_file.exists():
                logger.info(f"缩略图生成成功: {thumbnail_file}")
                return str(thumbnail_file)
            else:
                logger.warning(f"缩略图生成失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"生成缩略图异常: {e}")
            return None
