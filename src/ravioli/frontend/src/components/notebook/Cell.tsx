import React from 'react';
import { Play, RotateCcw, Trash2 } from 'lucide-react';
import Markdown from 'markdown-to-jsx';
import { clsx } from 'clsx';

interface CellProps {
  id: string;
  type: 'user' | 'agent';
  content: string;
  onExecute?: (id: string, value: string) => void;
  status?: 'idle' | 'executing' | 'completed' | 'error';
}

export const Cell: React.FC<CellProps> = ({ id, type, content, onExecute, status }) => {
  const [inputValue, setInputValue] = React.useState(content);

  return (
    <div className={clsx(
      "group relative mb-8 rounded-md transition-all",
      type === 'agent' ? "glass p-6" : "surface-lowest p-4"
    )}>
      {/* Label/Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="label text-[#a38b88]">
            {type === 'user' ? 'User Inquiry' : 'Agent Response'}
          </span>
          {status === 'executing' && (
            <div className="w-2 h-2 rounded-full bg-[#eac34a] animate-pulse" />
          )}
        </div>
        
        <div className="flex items-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="text-[#a38b88] hover:text-white"><RotateCcw size={14} /></button>
          <button className="text-[#a38b88] hover:text-[#ffb3b5]"><Trash2 size={14} /></button>
        </div>
      </div>

      {/* Content Area */}
      {type === 'user' ? (
        <div className="flex gap-4 items-start">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="flex-1 min-h-[60px] resize-none text-white leading-relaxed"
            placeholder="Ask a question..."
          />
          <button 
            onClick={() => onExecute?.(id, inputValue)}
            disabled={status === 'executing'}
            className="btn-gold p-2 rounded-sm flex items-center justify-center disabled:opacity-50"
          >
            <Play size={16} fill="currentColor" />
          </button>
        </div>
      ) : (
        <div className="prose prose-invert max-w-none text-[#d1d5db] leading-relaxed">
          <Markdown>{content}</Markdown>
        </div>
      )}
    </div>
  );
};
