'use client';

import React, { useState, useEffect } from 'react';
import { Camera, X, CheckCircle2, Loader2, ShieldAlert, AlertCircle } from 'lucide-react';

interface UploadOverlayProps {
  onClose: () => void;
  onSuccess: (documentId: string) => void;
  memberId: string;
  apiClient: any;
}

export const UploadOverlay: React.FC<UploadOverlayProps> = ({
  onClose,
  onSuccess,
  memberId,
  apiClient,
}) => {
  const [step, setStep] = useState<'idle' | 'uploading' | 'processing' | 'done' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [errorHeader, setErrorHeader] = useState('提取失败');
  const [errorMessage, setErrorMessage] = useState('智能服务暂不可用，请稍后重试或手动录入。');

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setStep('uploading');
    setProgress(20);

    try {
      // 模拟上传进度
      const uploadInterval = setInterval(() => {
        setProgress(prev => (prev < 90 ? prev + 10 : prev));
      }, 500);

      const uploadRes = await apiClient.uploadDocument(file, memberId);
      clearInterval(uploadInterval);
      setProgress(100);

      setStep('processing');
      // 模拟 OCR 处理
      await apiClient.submitOcr(uploadRes.document_id);
      
      setStep('done');
      setTimeout(() => {
        onSuccess(uploadRes.document_id);
        onClose();
      }, 1500);

    } catch (err: any) {
      setStep('error');
      setErrorHeader('智能提取失败');
      setErrorMessage(err.message || '识别过程中发生错误');
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-300"
        onClick={onClose}
      ></div>
      
      <div className="relative w-full max-w-sm glass-card rounded-[32px] p-8 shadow-2xl animate-in zoom-in slide-in-from-bottom-8 duration-500">
        {step === 'idle' && (
          <div className="space-y-6 text-center">
            <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto text-blue-600">
              <Camera size={36} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">上传检查单</h2>
              <p className="text-sm text-slate-500 mt-2">支持 JPG、PNG 图片，我们将自动提取指标</p>
            </div>
            <label className="block w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-2xl font-bold cursor-pointer transition-all shadow-xl shadow-blue-500/30">
              选择照片
              <input type="file" accept="image/*" className="hidden" onChange={handleFileSelect} />
            </label>
            <button onClick={onClose} className="text-slate-400 font-medium text-sm">取消</button>
          </div>
        )}

        {(step === 'uploading' || step === 'processing') && (
          <div className="space-y-8 py-4">
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <Loader2 size={48} className="text-blue-500 animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                </div>
              </div>
              <div className="text-center">
                <h3 className="text-lg font-bold text-slate-800">
                  {step === 'uploading' ? '正在上传文件...' : '正在智能分析...'}
                </h3>
                <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-bold">
                  {step === 'uploading' ? `进度 ${progress}%` : '基于 Qwen2.5-VL 处理中'}
                </p>
              </div>
            </div>
            
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-500 ease-out" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <div className="space-y-3">
               <div className="flex items-center gap-3 text-xs">
                  <div className={`w-2 h-2 rounded-full ${progress >= 30 ? 'bg-green-500' : 'bg-slate-300'}`}></div>
                  <span className={progress >= 30 ? 'text-slate-600' : 'text-slate-400'}>安全脱敏处理</span>
               </div>
               <div className="flex items-center gap-3 text-xs">
                  <div className={`w-2 h-2 rounded-full ${step === 'processing' ? 'bg-green-500' : 'bg-slate-300'}`}></div>
                  <span className={step === 'processing' ? 'text-slate-600' : 'text-slate-400'}>视觉结构化提取</span>
               </div>
            </div>
          </div>
        )}

        {step === 'done' && (
          <div className="space-y-6 text-center py-4">
            <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto text-green-500">
              <CheckCircle2 size={48} className="animate-in zoom-in duration-500" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800 tracking-tight">分析完成</h2>
              <p className="text-sm text-slate-500 mt-2">点击“去审核”或稍后在看板查看</p>
            </div>
          </div>
        )}

        {step === 'error' && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-red-600 mb-2">
              <ShieldAlert size={32} />
              <h2 className="text-lg font-bold">{errorHeader}</h2>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">{errorMessage}</p>
            <div className="flex gap-3 pt-2">
              <button onClick={() => setStep('idle')} className="flex-1 bg-slate-100 text-slate-600 py-3 rounded-xl font-bold">重试</button>
              <button onClick={onClose} className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-bold">手动录入</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
