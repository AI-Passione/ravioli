import React from 'react';
import { Cell } from './Cell';
import { Plus } from 'lucide-react';

interface Log {
  id: string;
  type: 'user' | 'agent';
  content: string;
  status?: 'idle' | 'executing' | 'completed' | 'error';
}

interface NotebookProps {
  missionTitle: string;
  logs: Log[];
  onExecuteCell: (cellId: string, value: string) => void;
  onAddCell: () => void;
}

export const Notebook: React.FC<NotebookProps> = ({ 
  missionTitle, 
  logs, 
  onExecuteCell,
  onAddCell
}) => {
  return (
    <div className="pb-32">
      <header className="mb-16">
        <h2 className="text-4xl mb-2 text-white">{missionTitle}</h2>
        <div className="flex items-center gap-4">
          <span className="label text-[#eac34a]">Mission Active</span>
          <span className="label text-[#554240]"># {logs.length} Steps</span>
        </div>
      </header>

      <div className="space-y-4">
        {logs.map(log => (
          <Cell 
            key={log.id}
            id={log.id}
            type={log.type}
            content={log.content}
            status={log.status}
            onExecute={onExecuteCell}
          />
        ))}
      </div>

      <button 
        onClick={onAddCell}
        className="mt-10 w-full py-4 rounded-md border-1 border-dashed border-[#554240] text-[#a38b88] hover:text-white hover:bg-[#1c1b1b] transition-all flex items-center justify-center gap-2 label"
      >
        <Plus size={16} />
        Add Interaction Step
      </button>
    </div>
  );
};
