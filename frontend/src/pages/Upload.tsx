import React, { useState } from 'react';
import { Upload as UploadIcon, Video, Scissors, CheckCircle, X } from 'lucide-react';
import clsx from 'clsx';

export const Upload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [step, setStep] = useState<'select' | 'config' | 'uploading' | 'complete'>('select');
  const [splitMode, setSplitMode] = useState<'auto' | 'manual' | 'hybrid'>('hybrid');
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStep('config');
    }
  };

  const handleUpload = () => {
    setStep('uploading');
    // Simulate upload
    let p = 0;
    const interval = setInterval(() => {
      p += 5;
      if (p >= 100) {
        clearInterval(interval);
        setStep('complete');
      }
      setProgress(p);
    }, 100);
  };

  return (
    <div className="flex flex-col h-full bg-white pb-20">
      <div className="p-4 flex items-center justify-between border-b">
        <X size={24} className="text-gray-500" onClick={() => setFile(null)} />
        <h1 className="font-bold text-lg">上传视频</h1>
        <div className="w-6" /> {/* Spacer */}
      </div>

      <div className="flex-1 flex flex-col p-6">
        {step === 'select' && (
          <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer relative">
            <input 
              type="file" 
              accept="video/*" 
              className="absolute inset-0 opacity-0 cursor-pointer"
              onChange={handleFileChange}
            />
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center text-blue-500 mb-4">
              <UploadIcon size={40} />
            </div>
            <p className="text-gray-500 font-medium mb-2">点击或拖拽上传视频</p>
            <p className="text-gray-400 text-sm">支持 MP4, MOV 等格式</p>
          </div>
        )}

        {step === 'config' && file && (
          <div className="flex-1 flex flex-col gap-6">
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl">
              <div className="w-20 h-20 bg-black rounded-lg flex items-center justify-center">
                 <Video className="text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold truncate">{file.name}</h3>
                <p className="text-sm text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>

            <div>
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <Scissors size={18} />
                智能拆分设置
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'auto', label: '全自动', desc: 'AI自动识别场景' },
                  { id: 'hybrid', label: '混合模式', desc: '自动识别+人工微调' },
                  { id: 'manual', label: '纯手动', desc: '手动标记拆分点' }
                ].map((mode) => (
                  <button
                    key={mode.id}
                    onClick={() => setSplitMode(mode.id as any)}
                    className={clsx(
                      "flex flex-col items-center justify-center p-3 rounded-xl border-2 transition-all",
                      splitMode === mode.id 
                        ? "border-blue-500 bg-blue-50 text-blue-600" 
                        : "border-gray-200 text-gray-500"
                    )}
                  >
                    <span className="font-bold text-sm mb-1">{mode.label}</span>
                    <span className="text-[10px] text-center opacity-80">{mode.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-auto">
              <button 
                onClick={handleUpload}
                className="w-full bg-blue-600 text-white py-4 rounded-full font-bold text-lg shadow-lg hover:bg-blue-700 active:scale-95 transition-all"
              >
                开始上传并处理
              </button>
            </div>
          </div>
        )}

        {step === 'uploading' && (
          <div className="flex-1 flex flex-col items-center justify-center">
             <div className="w-32 h-32 relative flex items-center justify-center mb-8">
               <svg className="w-full h-full transform -rotate-90">
                 <circle cx="64" cy="64" r="60" stroke="#eee" strokeWidth="8" fill="none" />
                 <circle 
                   cx="64" cy="64" r="60" 
                   stroke="#2563eb" strokeWidth="8" fill="none" 
                   strokeDasharray={2 * Math.PI * 60}
                   strokeDashoffset={2 * Math.PI * 60 * (1 - progress / 100)}
                   className="transition-all duration-300"
                 />
               </svg>
               <span className="absolute text-2xl font-bold text-blue-600">{progress}%</span>
             </div>
             <h3 className="text-xl font-bold mb-2">正在上传视频...</h3>
             <p className="text-gray-500">请勿关闭页面，上传完成后将自动开始拆分</p>
          </div>
        )}

        {step === 'complete' && (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center text-green-500 mb-6 animate-bounce">
              <CheckCircle size={48} />
            </div>
            <h3 className="text-2xl font-bold mb-2">上传成功！</h3>
            <p className="text-gray-500 mb-8 max-w-xs">您的视频已进入处理队列，AI 正在为您智能拆分视频。完成后将通过消息通知您。</p>
            
            <div className="flex flex-col w-full gap-3">
              <button onClick={() => window.location.href = '/inbox'} className="w-full bg-blue-600 text-white py-3 rounded-full font-bold">
                查看任务状态
              </button>
              <button onClick={() => { setFile(null); setStep('select'); }} className="w-full bg-gray-100 text-gray-600 py-3 rounded-full font-bold">
                继续上传
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
