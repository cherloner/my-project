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

interface LearnRecord {
  video_id: string;
  video_title: string;
  cover_url: string;
  status: 'learned' | 'review_needed';
  last_watch_time: string;
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

// Helper to write DB
const writeDb = async (records: LearnRecord[]) => {
  try {
    await fs.writeJson(DB_FILE, records, { spaces: 2 });
  } catch (e) {
    console.error("Failed to write DB", e);
  }
};

const app = express();
const PORT = 8000;

// Enable CORS
app.use(cors());

// Parse JSON bodies (for init/complete)
app.use(express.json());

// Path to store uploaded files
const UPLOAD_DIR = path.join(__dirname, '../uploads');
const TEMP_DIR = path.join(UPLOAD_DIR, 'temp');
const FINAL_DIR = path.join(UPLOAD_DIR, 'final');

// Ensure directories exist
fs.ensureDirSync(TEMP_DIR);
fs.ensureDirSync(FINAL_DIR);

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
        upload_url: `http://localhost:${PORT}/api/upload/chunk`,
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

app.get('/api/feed/recommend', (req, res) => res.json({ code: 200, data: { items: [] } }));

app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
  console.log(`Uploads stored in ${UPLOAD_DIR}`);
});
