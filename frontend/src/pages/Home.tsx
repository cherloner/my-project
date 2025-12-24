import React, { useState, useEffect, useRef } from 'react';
import { MOCK_VIDEOS } from '../services/mockData';
import { VideoPlayer } from '../components/VideoPlayer';

export const Home: React.FC = () => {
  const [activeindex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const index = Math.round(container.scrollTop / container.clientHeight);
      if (index !== activeindex) {
        setActiveIndex(index);
      }
    };

    // Use IntersectionObserver for better performance? 
    // For simplicity, scroll event with debounce/round is okay for demo
    // Actually, snap scroll handles the movement, we just need to detect which one is active.
    
    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [activeindex]);

  return (
    <div 
      ref={containerRef}
      className="h-full w-full overflow-y-scroll snap-y snap-mandatory no-scrollbar"
      style={{ scrollBehavior: 'smooth' }}
    >
      {MOCK_VIDEOS.map((video, index) => (
        <div key={video.id} className="w-full h-full snap-start">
          <VideoPlayer video={video} isActive={index === activeindex} />
        </div>
      ))}
    </div>
  );
};
