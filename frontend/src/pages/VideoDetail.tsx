import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { VideoLearningPlayer } from '../components/VideoLearningPlayer';
import { MOCK_VIDEOS } from '../services/mockData';

export const VideoDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Find mock video data or use default
  const video = MOCK_VIDEOS.find(v => v.id === id) || MOCK_VIDEOS[0];

  const handleComplete = () => {
    // Navigate back after completion or stay
    // navigate(-1); 
  };

  return (
    <div className="flex flex-col h-screen bg-black text-white">
      {/* Navbar */}
      <div className="flex items-center p-4 sticky top-0 z-10 bg-gradient-to-b from-black/80 to-transparent">
        <button 
          onClick={() => navigate(-1)} 
          className="p-2 -ml-2 rounded-full hover:bg-white/10 transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
        <span className="ml-2 font-bold truncate flex-1">{video.title}</span>
      </div>

      {/* Player Area */}
      <div className="flex-1 flex flex-col justify-center">
        <VideoLearningPlayer
          videoId={id || ''}
          onComplete={handleComplete}
        />
        
        <div className="p-6">
          <h1 className="text-xl font-bold mb-2">{video.title}</h1>
          <div className="flex items-center gap-3 mb-4">
            <img src={video.author.avatar} className="w-8 h-8 rounded-full border border-white/20" alt="author" />
            <span className="text-sm text-gray-300">{video.author.name}</span>
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">
            {video.description}
          </p>
        </div>
      </div>
    </div>
  );
};
