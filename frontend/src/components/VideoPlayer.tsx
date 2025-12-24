import React, { useRef, useState, useEffect } from 'react';
import { Heart, MessageCircle, Share2, Play } from 'lucide-react';
import type { Video } from '../services/mockData';

interface VideoPlayerProps {
  video: Video;
  isActive: boolean;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({ video, isActive }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (isActive) {
      videoRef.current?.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    } else {
      videoRef.current?.pause();
      setIsPlaying(false);
      if (videoRef.current) videoRef.current.currentTime = 0;
    }
  }, [isActive]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const progress = (videoRef.current.currentTime / videoRef.current.duration) * 100;
      setProgress(progress);
    }
  };

  return (
    <div className="relative w-full h-full bg-black snap-start shrink-0">
      {/* Video Element */}
      <video
        ref={videoRef}
        src={video.url}
        className="w-full h-full object-cover"
        loop
        playsInline
        onClick={togglePlay}
        onTimeUpdate={handleTimeUpdate}
        poster={video.cover}
      />

      {/* Play/Pause Overlay Icon */}
      {!isPlaying && (
        <div 
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
        >
          <div className="bg-black/30 p-4 rounded-full backdrop-blur-sm">
            <Play fill="white" size={48} className="text-white ml-1" />
          </div>
        </div>
      )}

      {/* Side Actions */}
      <div className="absolute right-2 bottom-20 flex flex-col items-center gap-6 z-10">
        <div className="relative">
          <img 
            src={video.author.avatar} 
            alt={video.author.name} 
            className="w-12 h-12 rounded-full border-2 border-white object-cover"
          />
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-red-500 rounded-full p-0.5">
             <div className="w-3 h-3 flex items-center justify-center text-white text-[10px]">+</div>
          </div>
        </div>
        
        <div className="flex flex-col items-center gap-1">
          <Heart size={32} className="text-white drop-shadow-md" />
          <span className="text-white text-xs font-medium drop-shadow-md">{video.likes}</span>
        </div>

        <div className="flex flex-col items-center gap-1">
          <MessageCircle size={32} className="text-white drop-shadow-md" />
          <span className="text-white text-xs font-medium drop-shadow-md">{video.comments}</span>
        </div>

        <div className="flex flex-col items-center gap-1">
          <Share2 size={32} className="text-white drop-shadow-md" />
          <span className="text-white text-xs font-medium drop-shadow-md">{video.shares}</span>
        </div>
      </div>

      {/* Bottom Info */}
      <div className="absolute left-4 bottom-6 right-16 z-10 text-white">
        <h3 className="font-bold text-lg mb-2 drop-shadow-md">@{video.author.name}</h3>
        <p className="text-sm mb-2 drop-shadow-md line-clamp-2">{video.description}</p>
        <div className="flex items-center gap-2 text-xs opacity-80">
           <span className="bg-white/20 px-2 py-1 rounded backdrop-blur-sm">♫ 原始原声 - {video.author.name}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
        <div 
          className="h-full bg-white transition-all duration-100 ease-linear"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
