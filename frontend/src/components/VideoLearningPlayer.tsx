import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, CheckCircle, HelpCircle, X, Loader2 } from 'lucide-react';
import { videoApi, learnApi } from '../services/api';

// --- Types ---
interface VideoDetail {
  id: string;
  title: string;
  play_url: string;
  cover_url?: string;
  last_position: number; // Seconds
}

interface HeartbeatPayload {
  video_id: string;
  position: number;
  buffered: number;
  playing: boolean;
}

interface VideoLearningPlayerProps {
  videoId: string;
  onComplete?: (status: 'learned' | 'review_needed') => void;
}

export const VideoLearningPlayer: React.FC<VideoLearningPlayerProps> = ({ 
  videoId, 
  onComplete 
}) => {
  // --- Refs ---
  const videoRef = useRef<HTMLVideoElement>(null);
  const positionRef = useRef(0); // Store current position for cleanup closure
  const heartbeatTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasCompletedRef = useRef(false); // Ref to avoid state closure issues

  // --- State ---
  const [videoData, setVideoData] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0); // Visual progress 0-100
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showCompleteModal, setShowCompleteModal] = useState(false);

  // Heartbeat Status State
  const [heartbeatStatus, setHeartbeatStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');
  const [lastHeartbeatTime, setLastHeartbeatTime] = useState<Date | null>(null);

  // --- 1. Initialization: Fetch Video & Last Position ---
  useEffect(() => {
    let mounted = true;
    
    const fetchVideo = async () => {
      try {
        setLoading(true);
        // Note: In real app, response.data would match VideoDetail structure
        const res = await videoApi.getVideoDetail(videoId);
        
        if (mounted && res.data) {
          // Adapt mock or real data
          const data: VideoDetail = {
            id: res.data.id,
            title: res.data.title,
            play_url: res.data.url || res.data.play_url, // Fallback
            cover_url: res.data.cover || res.data.cover_url,
            last_position: res.data.last_position || 0
          };
          setVideoData(data);
        }
      } catch (error) {
        console.error('Failed to load video', error);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchVideo();

    return () => { mounted = false; };
  }, [videoId]);

  // --- Auto-Seek on Load ---
  const handleLoadedMetadata = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    const video = e.currentTarget;
    setDuration(video.duration);
    
    if (videoData?.last_position && videoData.last_position > 0) {
      video.currentTime = videoData.last_position;
      setCurrentTime(videoData.last_position);
    }
  };

  // --- 2. Heartbeat System ---
  const sendHeartbeat = async (playing: boolean, forcePosition?: number) => {
    // Use ref or forcePosition to get latest value without state dependency
    const pos = forcePosition ?? positionRef.current;
    
    // Calculate buffered
    let buffered = 0;
    if (videoRef.current && videoRef.current.buffered.length > 0) {
      buffered = videoRef.current.buffered.end(videoRef.current.buffered.length - 1);
    }

    const payload: HeartbeatPayload = {
      video_id: videoId,
      position: pos,
      buffered: buffered,
      playing: playing
    };

    try {
      setHeartbeatStatus('sending');
      await learnApi.sendHeartbeat(payload);
      console.log('💓 Heartbeat sent:', payload);
      setHeartbeatStatus('success');
      setLastHeartbeatTime(new Date());
      // Reset status to idle after 2 seconds
      setTimeout(() => setHeartbeatStatus('idle'), 2000);
    } catch (error) {
      // Fail silently for heartbeat
      setHeartbeatStatus('error');
    }
  };

  // Timer Effect
  useEffect(() => {
    if (isPlaying) {
      // Send immediately on start
      sendHeartbeat(true);

      // Schedule every 10s
      heartbeatTimerRef.current = setInterval(() => {
        sendHeartbeat(true);
      }, 10000);
    } else {
      // Clear when paused
      if (heartbeatTimerRef.current) {
        clearInterval(heartbeatTimerRef.current);
        heartbeatTimerRef.current = null;
      }
    }

    return () => {
      if (heartbeatTimerRef.current) {
        clearInterval(heartbeatTimerRef.current);
      }
    };
  }, [isPlaying, videoId]);

  // Cleanup & AppState Listener Effect
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // App went to background -> Force heartbeat
        sendHeartbeat(false);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      
      // Component Unmount -> Force heartbeat
      // Reading from positionRef.current ensures we have latest value even in closure
      console.log('🛑 Player unmount cleanup');
      sendHeartbeat(false);
    };
  }, [videoId]);


  // --- 3. Completion Logic & Progress ---
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const curr = videoRef.current.currentTime;
      const dur = videoRef.current.duration;
      
      // Update Ref for cleanup access
      positionRef.current = curr;

      // Update State for UI
      setCurrentTime(curr);
      setProgress((curr / dur) * 100);

      // Check Completion (>= 90%)
      if (!hasCompletedRef.current && dur > 0 && (curr / dur) >= 0.9) {
        handleReachCompletion();
      }
    }
  };

  const handleReachCompletion = () => {
    hasCompletedRef.current = true;
    if (videoRef.current) {
      videoRef.current.pause();
      setIsPlaying(false);
    }
    console.log('🎉 90% reached, showing modal');
    setShowCompleteModal(true);
  };

  const handleCompletionChoice = async (status: 'learned' | 'review_needed') => {
    try {
      await learnApi.completeLearn({
        video_id: videoId,
        status: status
      });
      setShowCompleteModal(false);
      if (onComplete) onComplete(status);
    } catch (error) {
      console.error('Failed to complete', error);
      alert('提交失败，请重试');
    }
  };

  // --- UI Controls ---
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

  // Format seconds to MM:SS
  const formatTime = (time: number) => {
    if (isNaN(time)) return '0:00';
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (loading) {
    return (
      <div className="w-full aspect-video bg-gray-900 rounded-xl flex items-center justify-center text-white">
        <Loader2 className="animate-spin mr-2" />
        加载视频中...
      </div>
    );
  }

  if (!videoData) {
    return (
      <div className="w-full aspect-video bg-gray-900 rounded-xl flex items-center justify-center text-white">
        <X className="mr-2" />
        视频加载失败
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden shadow-lg group">
      <video
        ref={videoRef}
        src={videoData.play_url}
        poster={videoData.cover_url}
        className="w-full h-full object-contain"
        playsInline
        onClick={togglePlay}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => {
          setIsPlaying(false);
          sendHeartbeat(false);
        }}
        onEnded={() => setIsPlaying(false)}
      />



      {/* Heartbeat Status Indicator (Top Right) */}
      <div className="absolute top-4 right-4 z-20 flex flex-col items-end pointer-events-none">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full backdrop-blur-md transition-all duration-300 ${
            heartbeatStatus === 'error' ? "bg-red-500/80 text-white" :
            heartbeatStatus === 'sending' ? "bg-blue-500/80 text-white" :
            heartbeatStatus === 'success' ? "bg-green-500/80 text-white" :
            "bg-black/40 text-gray-200"
          }`}
        >
          {heartbeatStatus === 'sending' && <Loader2 size={12} className="animate-spin" />}
          {heartbeatStatus === 'success' && <CheckCircle size={12} />}
          {heartbeatStatus === 'error' && <X size={12} />}
          {heartbeatStatus === 'idle' && <HelpCircle size={12} />}
          
          <span className="text-[10px] font-medium font-mono">
            {heartbeatStatus === 'sending' ? '同步中...' :
             heartbeatStatus === 'success' ? '已同步' :
             heartbeatStatus === 'error' ? '同步失败' :
             '学习监控中'}
          </span>
        </div>
        {lastHeartbeatTime && (
          <span className="text-[9px] text-white/60 mt-1 mr-2 font-mono">
            上次同步: {lastHeartbeatTime.toLocaleTimeString([], { hour12: false })}
          </span>
        )}
      </div>

      {/* Center Play Button (Overlay) */}
      {!isPlaying && !showCompleteModal && (
        <div 
          className="absolute inset-0 flex items-center justify-center bg-black/30 cursor-pointer"
          onClick={togglePlay}
        >
          <div className="bg-white/20 backdrop-blur-sm p-4 rounded-full transition-transform hover:scale-110">
            <Play fill="white" size={48} className="text-white ml-1" />
          </div>
        </div>
      )}

      {/* Bottom Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="flex items-center gap-4 text-white">
          <button onClick={togglePlay}>
            {isPlaying ? <Pause size={24} fill="white" /> : <Play size={24} fill="white" />}
          </button>
          
          <div className="text-xs font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>

          <div className="flex-1 h-1 bg-gray-600 rounded-full overflow-hidden cursor-pointer relative group/progress">
            <div 
              className="h-full bg-blue-500 relative" 
              style={{ width: `${progress}%` }}
            >
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow opacity-0 group-hover/progress:opacity-100 transition-opacity" />
            </div>
            
            {/* Interactive Range Input */}
            <input 
              type="range" 
              min="0" 
              max="100" 
              step="0.1"
              value={progress}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setProgress(val);
                if (videoRef.current && videoRef.current.duration) {
                  const newTime = (val / 100) * videoRef.current.duration;
                  videoRef.current.currentTime = newTime;
                  // Trigger completion check manually on seek
                  if (!hasCompletedRef.current && videoRef.current.duration > 0 && (newTime / videoRef.current.duration) >= 0.9) {
                    handleReachCompletion();
                  }
                }
              }}
              onClick={(e) => e.stopPropagation()}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
            />
          </div>
        </div>
      </div>

      {/* Completion Modal */}
      {showCompleteModal && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in zoom-in duration-300">
          <div className="bg-white rounded-2xl p-6 w-[80%] max-w-sm shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">恭喜！已学习 90%</h3>
              <button onClick={() => setShowCompleteModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            
            <p className="text-gray-600 text-sm mb-6">
              您已完成本节课的大部分内容，请评估您的学习效果：
            </p>

            <div className="space-y-3">
              <button
                onClick={() => handleCompletionChoice('learned')}
                className="w-full flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600 text-white py-3 rounded-xl font-bold transition-colors"
              >
                <CheckCircle size={20} />
                我已学会
              </button>
              
              <button
                onClick={() => handleCompletionChoice('review_needed')}
                className="w-full flex items-center justify-center gap-2 bg-amber-100 hover:bg-amber-200 text-amber-700 py-3 rounded-xl font-bold transition-colors"
              >
                <HelpCircle size={20} />
                需复习
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
