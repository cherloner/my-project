import express, { Request, Response } from 'express';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs-extra';
import path from 'path';
import stream from 'stream';
import { promisify } from 'util';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const pipeline = promisify(stream.pipeline);

// --- Persistent Mock Database (JSON) ---
const DB_FILE = path.join(__dirname, '../db.json');
const VIDEOS_DB_FILE = path.join(__dirname, '../videos.json');
const USERS_DB_FILE = path.join(__dirname, '../users.json');

interface LearnRecord {
  video_id: string;
  video_title: string;
  cover_url: string;
  status: 'learned' | 'review_needed';
  last_watch_time: string;
}

interface UserRecord {
  id: string;
  phone: string;
  nickname: string;
  avatar: string;
  bio?: string;
  gender?: 'male' | 'female' | 'other';
  location?: string;
  school?: string;
}

interface VideoRecord {
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
  created_at: string;
}

// Helper to read DB
const readDb = async (): Promise<LearnRecord[]> => {
  try {
    if (await fs.pathExists(DB_FILE)) {
      return await fs.readJson(DB_FILE);
    }
  } catch (e) {
    console.error("Failed to read DB", e);
  }
  return [];
};

const readVideosDb = async (): Promise<VideoRecord[]> => {
  try {
    if (await fs.pathExists(VIDEOS_DB_FILE)) {
      return await fs.readJson(VIDEOS_DB_FILE);
    }
  } catch (e) {
    console.error("Failed to read Videos DB", e);
  }
  return [];
};

const readUsersDb = async (): Promise<UserRecord[]> => {
  try {
    if (await fs.pathExists(USERS_DB_FILE)) {
      return await fs.readJson(USERS_DB_FILE);
    }
  } catch (e) {
    console.error("Failed to read Users DB", e);
  }
  // Default mock user if empty
  return [{
    id: 'u1',
    phone: '13800138000',
    nickname: '测试用户',
    avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&q=80',
    bio: '热爱编程，分享技术 | 全栈开发者',
    gender: 'male',
    location: '北京',
    school: '清华大学'
  }];
};

// Helper to write DB
const writeDb = async (records: LearnRecord[]) => {
  try {
    await fs.writeJson(DB_FILE, records, { spaces: 2 });
  } catch (e) {
    console.error("Failed to write DB", e);
  }
};

const writeVideosDb = async (records: VideoRecord[]) => {
  try {
    await fs.writeJson(VIDEOS_DB_FILE, records, { spaces: 2 });
  } catch (e) {
    console.error("Failed to write Videos DB", e);
  }
};

const writeUsersDb = async (records: UserRecord[]) => {
  try {
    await fs.writeJson(USERS_DB_FILE, records, { spaces: 2 });
  } catch (e) {
    console.error("Failed to write Users DB", e);
  }
};

// Initialize DBs
const initDB = async () => {
  try {
    if (!await fs.pathExists(USERS_DB_FILE)) {
      await fs.writeJson(USERS_DB_FILE, [{
        id: 'u1',
        phone: '13800138000',
        nickname: '测试用户',
        avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&q=80',
        bio: '热爱编程，分享技术 | 全栈开发者',
        gender: 'male',
        location: '北京',
        school: '清华大学'
      }], { spaces: 2 });
      console.log("Initialized users.json");
    }
  } catch (e) {
    console.error("Failed to init DB", e);
  }
};
initDB();

const app = express();
const PORT = 8000;

// Enable CORS
app.use(cors({
  origin: '*', // Allow all origins for dev
  allowedHeaders: ['Content-Type', 'Authorization', 'upload_id', 'chunk_index']
}));

// Parse JSON bodies (increase limit to allow base64 images)
app.use(express.json({ limit: '30mb' }));

// Path to store uploaded files
const UPLOAD_DIR = path.join(__dirname, '../uploads');
const TEMP_DIR = path.join(UPLOAD_DIR, 'temp');
const FINAL_DIR = path.join(UPLOAD_DIR, 'final');

// Ensure directories exist
fs.ensureDirSync(TEMP_DIR);
fs.ensureDirSync(FINAL_DIR);

// Serve static video files
app.use('/api/videos/file', express.static(FINAL_DIR));

/**
 * Interface for Init Request
 */
interface InitRequest {
  file_name: string;
  file_size: number;
  duration: number;
  mime_type: string;
}

/**
 * 1. Initialize Upload
 * POST /api/upload/init
 */
app.post('/api/upload/init', async (req: Request, res: Response) => {
  try {
    const { file_name, file_size, duration, mime_type }: InitRequest = req.body;
    
    // Generate unique upload ID
    const upload_id = uuidv4();
    
    // Create temp directory for this upload
    const uploadDir = path.join(TEMP_DIR, upload_id);
    await fs.ensureDir(uploadDir);

    console.log(`[Init] New upload started: ${upload_id} (${file_name})`);

    res.json({
      code: 200,
      message: "success",
      data: {
        upload_id,
        // Return relative path so frontend uses its proxy (and baseURL '/api')
        upload_url: `upload/chunk`, 
        chunk_size: 2 * 1024 * 1024 // 2MB recommendation
      }
    });
  } catch (error: any) {
    console.error('[Init] Error:', error);
    res.status(500).json({ code: 500, message: error.message });
  }
});

/**
 * 2. Upload Chunk
 * PUT /api/upload/chunk
 */
app.put('/api/upload/chunk', async (req: Request, res: Response) => {
  try {
    const upload_id = req.headers['upload_id'] as string;
    const chunk_index = req.headers['chunk_index'] as string;

    if (!upload_id || chunk_index === undefined) {
      res.status(400).json({ code: 400, message: "Missing upload_id or chunk_index header" });
      return;
    }

    const chunkPath = path.join(TEMP_DIR, upload_id, chunk_index);

    // Create a write stream to save the chunk
    const writeStream = fs.createWriteStream(chunkPath);
    
    // Pipe request body (binary) to file
    await pipeline(req, writeStream);

    console.log(`[Chunk] Received chunk ${chunk_index} for ${upload_id}`);
    
    res.status(200).json({ code: 200, message: "success" });
  } catch (error: any) {
    console.error('[Chunk] Error:', error);
    res.status(500).json({ code: 500, message: error.message });
  }
});

/**
 * 3. Complete Upload (Merge)
 * POST /api/upload/complete
 */
app.post('/api/upload/complete', async (req: Request, res: Response) => {
  try {
    const { upload_id } = req.body;
    
    if (!upload_id) {
       res.status(400).json({ code: 400, message: "Missing upload_id" });
       return;
    }

    const uploadDir = path.join(TEMP_DIR, upload_id);
    
    // Check if directory exists
    if (!await fs.pathExists(uploadDir)) {
      res.status(404).json({ code: 404, message: "Upload session not found" });
      return;
    }

    // Get all chunk files and sort them numerically
    const chunks = await fs.readdir(uploadDir);
    const sortedChunks = chunks
      .filter(f => !isNaN(Number(f)))
      .sort((a, b) => Number(a) - Number(b));

    if (sortedChunks.length === 0) {
      res.status(400).json({ code: 400, message: "No chunks found" });
      return;
    }

    // Final file path
    const video_id = uuidv4();
    const finalPath = path.join(FINAL_DIR, `${video_id}.mp4`);
    const writeStream = fs.createWriteStream(finalPath);

    console.log(`[Merge] Merging ${sortedChunks.length} chunks for ${upload_id}...`);

    // Merge chunks sequentially
    for (const chunk of sortedChunks) {
      const chunkPath = path.join(uploadDir, chunk);
      const data = await fs.readFile(chunkPath);
      writeStream.write(data);
    }
    
    writeStream.end();

    // Wait for stream to finish
    await new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });

    console.log(`[Merge] Success: ${finalPath}`);

    // Cleanup temp chunks
    await fs.remove(uploadDir);

    // Add to Videos DB
    const videos = await readVideosDb();
    const newVideo: VideoRecord = {
      id: video_id,
      title: `上传视频 ${new Date().toLocaleDateString()}`,
      description: '这是一个用户上传的视频内容',
      url: `/api/videos/file/${video_id}.mp4`, // Relative URL, proxied by frontend
      cover: 'https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=800&q=80', // Placeholder cover
      author: {
        id: 'u_me',
        name: '我',
        avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&q=80'
      },
      likes: 0,
      comments: 0,
      shares: 0,
      created_at: new Date().toISOString()
    };
    videos.unshift(newVideo); // Add to beginning
    await writeVideosDb(videos);

    res.json({
      code: 200,
      message: "success",
      data: {
        video_id,
        status: 'transcoding'
      }
    });

  } catch (error: any) {
    console.error('[Merge] Error:', error);
    res.status(500).json({ code: 500, message: error.message });
  }
});

// Mock Auth/Learn endpoints for frontend demo
app.post('/api/auth/send_code', (req, res) => {
    res.json({ code: 200, message: "验证码已发送", data: { success: true } });
});
app.post('/api/auth/login_by_phone', (req, res) => {
    res.json({ code: 200, message: "登录成功", data: { token: "mock-token", user: { id: "u1", nickname: "User" } } });
});
app.post('/api/learn/heartbeat', (req, res) => res.json({ code: 200 }));
/**
 * 4. Learn Complete
 * POST /api/learn/complete
 */
app.post('/api/learn/complete', async (req: Request, res: Response) => {
  try {
    const { video_id, status, title, cover } = req.body;
    // Assume user_id comes from auth middleware (mocked here)
    const user_id = "mock-user-id"; 

    console.log(`[Learn] Complete: User ${user_id} finished video ${video_id} with status ${status}`);

    const completed_at = new Date();
    let next_review = null;
    let message = "已完成学习";

    // Update Persistent DB
    const records = await readDb();
    const existingIndex = records.findIndex((r: LearnRecord) => r.video_id === video_id);
    
    const recordData: LearnRecord = {
      video_id,
      // Use provided title/cover or fallback
      video_title: title || (existingIndex >= 0 ? records[existingIndex].video_title : `视频 ${video_id}`),
      cover_url: cover || (existingIndex >= 0 ? records[existingIndex].cover_url : 'https://picsum.photos/400/225'),
      status,
      last_watch_time: completed_at.toISOString()
    };

    if (existingIndex >= 0) {
      records[existingIndex] = recordData;
    } else {
      records.push(recordData);
    }
    
    // Save back to file
    await writeDb(records);

    if (status === 'review_needed') {
      // Calculate next review time (Now + 24h)
      const nextDate = new Date();
      nextDate.setDate(nextDate.getDate() + 1);
      next_review = nextDate.toISOString();
      message = "已加入复习计划";
      
      // TODO: Insert into notifications table
      console.log(`[Learn] Scheduled review for ${video_id} at ${next_review}`);
    } else if (status === 'learned') {
      // TODO: Clear old review reminders
      message = "恭喜！已标记为学会";
    }

    // Response
    res.json({
      code: 200,
      message: "success",
      data: {
        success: true,
        video_id,
        status,
        completed_at,
        next_review,
        toast_message: message
      }
    });

  } catch (error: any) {
    console.error('[Learn] Error:', error);
    res.status(500).json({ code: 500, message: error.message });
  }
});

/**
 * 5. Get Learn Records
 * GET /api/learn/records
 */
app.get('/api/learn/records', async (req, res) => {
  const records = await readDb();
  res.json({
    code: 200,
    message: "success",
    data: records
  });
});

app.get('/api/feed/recommend', async (req, res) => {
  const videos = await readVideosDb();
  res.json({ 
    code: 200, 
    data: { 
      items: videos 
    } 
  });
});

/**
 * 9. Search Suggest & Search Videos
 * Simple search over mock + uploaded videos
 */
const MOCK_SEARCH_VIDEOS: VideoRecord[] = [
  {
    id: '1',
    title: '3分钟学习微积分',
    description: '快速掌握微积分基础概念，数学其实很有趣！ #微积分 #数学 #学习',
    url: '/videos/calculus.mp4',
    cover: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800&q=80',
    author: { id: 'u1', name: '数学之美', avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&q=80' },
    likes: 1240,
    comments: 45,
    shares: 88,
    created_at: new Date().toISOString()
  },
  {
    id: '2',
    title: '雅思3分钟学习',
    description: '雅思口语高分技巧，每天3分钟，轻松开口说英语！ #雅思 #英语 #口语',
    url: '/videos/ielts.mp4',
    cover: 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=800&q=80',
    author: { id: 'u2', name: '英语达人', avatar: 'https://images.unsplash.com/photo-1599566150163-29194dcaad36?w=100&q=80' },
    likes: 3500,
    comments: 120,
    shares: 500,
    created_at: new Date().toISOString()
  }
];

const getAllVideosForSearch = async (): Promise<VideoRecord[]> => {
  const uploaded = await readVideosDb();
  return [...MOCK_SEARCH_VIDEOS, ...uploaded];
};

app.get('/api/search/suggest', async (req, res) => {
  const q = (req.query.q as string || '').trim();
  if (!q) {
    res.json([]);
    return;
  }
  const base = [q, `${q} 教程`, `${q} 入门`, `${q} 提高`, `${q} 3分钟学`];
  // Deduplicate and cap
  const suggestions = Array.from(new Set(base)).slice(0, 8);
  res.json(suggestions);
});

app.get('/api/search/videos', async (req, res) => {
  const q = ((req.query.q as string) || '').trim().toLowerCase();
  const tags = ((req.query.tags as string) || '').split(',').filter(Boolean);
  const sort_by = (req.query.sort_by as string) || 'latest';
  const duration_range = (req.query.duration_range as string) || '';

  let items = await getAllVideosForSearch();

  // Filter by q
  if (q) {
    items = items.filter(v => 
      v.title.toLowerCase().includes(q) ||
      v.description.toLowerCase().includes(q) ||
      v.author.name.toLowerCase().includes(q)
    );
  }

  // Filter by tags (simple keyword match)
  if (tags.length > 0) {
    items = items.filter(v => {
      const text = `${v.title} ${v.description}`.toLowerCase();
      return tags.some(t => text.includes(t.toLowerCase()));
    });
  }

  // Duration filter: demo only, keep all
  // Sort
  if (sort_by === 'latest') {
    items = items.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
  } else if (sort_by === 'hot') {
    items = items.sort((a, b) => (b.likes + b.comments + b.shares) - (a.likes + a.comments + a.shares));
  }

  res.json(items);
});

app.get('/api/video/:id', async (req, res) => {
  const id = req.params.id;
  const all = await getAllVideosForSearch();
  const found = all.find(v => v.id === id);
  if (!found) {
    res.status(404).json({ code: 404, message: 'Video not found' });
    return;
  }
  res.json({
    id: found.id,
    title: found.title,
    url: found.url,
    cover: found.cover,
    last_position: 0
  });
});

/**
 * 6. User Profile
 * GET /api/user/me
 */
app.get('/api/user/me', async (req, res) => {
  try {
    // Mock auth: assume user is 'u1'
    const userId = 'u1';
    const users = await readUsersDb();
    let user = users.find(u => u.id === userId);
    
    if (!user) {
      // Create default if not exists
      user = users[0];
    }
    
    res.json({
      code: 200,
      data: user
    });
  } catch (error: any) {
    res.status(500).json({ code: 500, message: error.message });
  }
});

/**
 * 7. Update User Profile
 * POST /api/user/update
 */
app.post('/api/user/update', async (req, res) => {
  try {
    console.log("[User] Update request received:", req.body);
    const { nickname, bio, gender, location, school, avatar } = req.body;
    const userId = 'u1'; // Mock auth
    
    const users = await readUsersDb();
    console.log("[User] Current users count:", users.length);
    
    const index = users.findIndex(u => u.id === userId);
    
    if (index === -1) {
      console.error("[User] User not found:", userId);
      res.status(404).json({ code: 404, message: "User not found" });
      return;
    }
    
    // Update fields
    const updatedUser = {
      ...users[index],
      nickname: nickname || users[index].nickname,
      bio: bio !== undefined ? bio : users[index].bio,
      gender: gender || users[index].gender,
      location: location !== undefined ? location : users[index].location,
      school: school !== undefined ? school : users[index].school,
      avatar: avatar || users[index].avatar
    };
    
    users[index] = updatedUser;
    await writeUsersDb(users);
    console.log("[User] Updated successfully:", updatedUser.id);
    
    res.json({
      code: 200,
      message: "success",
      data: updatedUser
    });
  } catch (error: any) {
    console.error("[User] Update failed:", error);
    res.status(500).json({ code: 500, message: error.message });
  }
});

/**
 * 8. Upload Image (Base64)
 * POST /api/upload/image
 */
app.post('/api/upload/image', express.json({ limit: '10mb' }), async (req, res) => {
  try {
    const { image } = req.body; // Base64 string: "data:image/png;base64,..."
    if (!image) {
      res.status(400).json({ code: 400, message: "No image data" });
      return;
    }

    // Parse Base64
    const matches = image.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
    if (!matches || matches.length !== 3) {
      res.status(400).json({ code: 400, message: "Invalid base64 string" });
      return;
    }

    const type = matches[1];
    const buffer = Buffer.from(matches[2], 'base64');
    const extension = type.split('/')[1];
    const fileName = `${uuidv4()}.${extension}`;
    const filePath = path.join(FINAL_DIR, fileName);

    await fs.writeFile(filePath, buffer);

    res.json({
      code: 200,
      data: {
        url: `/api/videos/file/${fileName}` // Reuse static file server
      }
    });
  } catch (error: any) {
    console.error("Upload image failed", error);
    res.status(500).json({ code: 500, message: error.message });
  }
});

// Start Server
app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
  console.log(`Uploads stored in ${UPLOAD_DIR}`);
});
