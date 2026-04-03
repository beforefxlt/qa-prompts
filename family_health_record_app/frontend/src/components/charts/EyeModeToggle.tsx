'use client';

import React from 'react';

export type EyeMode = 'both' | 'left' | 'right';

interface EyeModeToggleProps {
  mode: EyeMode;
  onChange: (mode: EyeMode) => void;
}

const MODE_LABELS: Record<EyeMode, string> = {
  both: '双眼',
  left: '左眼',
  right: '右眼',
};

export const EyeModeToggle: React.FC<EyeModeToggleProps> = ({ mode, onChange }) => {
  return (
    <div className="inline-flex bg-slate-100 rounded-full p-1 gap-1">
      {(['both', 'left', 'right'] as EyeMode[]).map((m) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
            mode === m
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-slate-400 hover:text-slate-600'
          }`}
        >
          {MODE_LABELS[m]}
        </button>
      ))}
    </div>
  );
};
