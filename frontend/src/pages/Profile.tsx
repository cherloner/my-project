import React from 'react';
import { Settings, Share2, Bookmark, Grid, Lock, LogOut } from 'lucide-react';
import { MOCK_VIDEOS } from '../services/mockData';
import { useAuth } from '../context/AuthContext';

export const Profile: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="flex flex-col h-full bg-white pb-20 overflow-y-auto">
      {/* Header Actions */}
      <div className="flex justify-between items-center p-4 sticky top-0 bg-white z-10">
        <h1 className="font-bold text-lg">{user?.nickname || '我的'}</h1>
        <div className="flex gap-4">
          <Share2 size={24} />
          <button onClick={logout} title="退出登录">
             <LogOut size={24} className="text-red-500" />
          </button>
        </div>
      </div>

      {/* Profile Info */}
      <div className="flex flex-col items-center px-4 pb-6 border-b border-gray-100">
        <div className="w-24 h-24 rounded-full overflow-hidden bg-gray-200 mb-4 border-4 border-gray-50">
           <img src={user?.avatar || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&q=80"} alt="Avatar" className="w-full h-full object-cover" />
        </div>
        <h2 className="text-xl font-bold mb-1">@{user?.nickname || '用户'}</h2>
        <p className="text-sm text-gray-500 mb-4">热爱编程，分享技术 | 全栈开发者</p>

        
        <div className="flex gap-8 mb-6">
          <div className="flex flex-col items-center">
            <span className="font-bold text-lg">142</span>
            <span className="text-xs text-gray-500">关注</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="font-bold text-lg">1.2w</span>
            <span className="text-xs text-gray-500">粉丝</span>
          </div>
          <div className="flex flex-col items-center">
            <span className="font-bold text-lg">8.5k</span>
            <span className="text-xs text-gray-500">获赞</span>
          </div>
        </div>

        <div className="flex gap-2 w-full">
          <button className="flex-1 bg-gray-100 py-2 rounded font-medium text-sm">编辑资料</button>
          <button className="flex-1 bg-gray-100 py-2 rounded font-medium text-sm">添加朋友</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 sticky top-[60px] bg-white z-10">
        <div className="flex-1 flex items-center justify-center py-3 border-b-2 border-black">
          <Grid size={20} />
        </div>
        <div className="flex-1 flex items-center justify-center py-3 text-gray-400">
          <Bookmark size={20} />
        </div>
        <div className="flex-1 flex items-center justify-center py-3 text-gray-400">
          <Lock size={20} />
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-3 gap-0.5">
        {[...MOCK_VIDEOS, ...MOCK_VIDEOS, ...MOCK_VIDEOS].map((video, idx) => (
          <div key={idx} className="aspect-[3/4] bg-gray-200 relative">
             <img src={video.cover} alt="Cover" className="w-full h-full object-cover" />
             <div className="absolute bottom-1 left-1 text-white text-xs flex items-center gap-1 drop-shadow-md">
               <PlayCircleIcon size={10} />
               <span>{video.likes}</span>
             </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const PlayCircleIcon = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="5 3 19 12 5 21 5 3"></polygon>
  </svg>
);
