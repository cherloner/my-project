export interface Video {
  id: string;
  title: string;
  description: string;
  url: string;
  cover: string;
  author: {
    id: string;
    name: string;
    avatar: string;
  };
  likes: number;
  comments: number;
  shares: number;
}

export const MOCK_VIDEOS: Video[] = [
  {
    id: '1',
    title: 'Python 快速入门 - 变量与类型',
    description: '3分钟学会Python基础变量，新手必看！ #Python #编程',
    url: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4', // Placeholder
    cover: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&q=80',
    author: {
      id: 'u1',
      name: 'Python大师',
      avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&q=80',
    },
    likes: 1240,
    comments: 45,
    shares: 88,
  },
  {
    id: '2',
    title: 'Java 并发编程实战',
    description: '深入理解Java线程池，面试必问！',
    url: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/friday.mp4', // Placeholder
    cover: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&q=80',
    author: {
      id: 'u2',
      name: '后端架构师',
      avatar: 'https://images.unsplash.com/photo-1599566150163-29194dcaad36?w=100&q=80',
    },
    likes: 3500,
    comments: 120,
    shares: 500,
  },
   {
    id: '3',
    title: 'React Hooks 最佳实践',
    description: 'useEffect 怎么用才对？来看看这个视频。',
    url: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4', // Placeholder
    cover: 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800&q=80',
    author: {
      id: 'u3',
      name: '前端小哥',
      avatar: 'https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=100&q=80',
    },
    likes: 890,
    comments: 30,
    shares: 12,
  },
];
