import React from 'react';
import { LayoutDashboard, Database, Settings, Plus, MessageSquare } from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
  activeMissionId?: string;
  missions: Array<{ id: string; title: string }>;
  onSelectMission: (id: string) => void;
  onCreateMission: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeMissionId, 
  missions, 
  onSelectMission, 
  onCreateMission 
}) => {
  return (
    <aside className="w-64 h-screen surface-low flex flex-col pt-8 pb-4 px-4 overflow-y-auto">
      <div className="flex items-center gap-3 mb-10 px-2">
        <div className="w-8 h-8 rounded-sm bg-gradient-to-br from-[#ffb3b5] to-[#4c000f]" />
        <h1 className="text-xl font-display tracking-tight text-white">Ravioli</h1>
      </div>

      <nav className="space-y-8 flex-1">
        <section>
          <p className="label text-[#a38b88] mb-4 px-2">System</p>
          <ul className="space-y-1">
            <SidebarItem icon={<LayoutDashboard size={18} />} label="Missions" active />
            <SidebarItem icon={<Database size={18} />} label="Warehouse" />
            <SidebarItem icon={<Settings size={18} />} label="Settings" />
          </ul>
        </section>

        <section>
          <div className="flex items-center justify-between mb-4 px-2">
            <p className="label text-[#a38b88]">Missions</p>
            <button 
              onClick={onCreateMission}
              className="text-[#eac34a] hover:opacity-80 transition-opacity"
            >
              <Plus size={16} />
            </button>
          </div>
          <ul className="space-y-1">
            {missions.map(mission => (
              <li key={mission.id}>
                <button
                  onClick={() => onSelectMission(mission.id)}
                  className={clsx(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-sm text-sm transition-colors",
                    mission.id === activeMissionId 
                      ? "bg-[#2a2a2a] text-white" 
                      : "text-[#9ca3af] hover:bg-[#2a2a2a] hover:text-white"
                  )}
                >
                  <MessageSquare size={14} className="opacity-60" />
                  <span className="truncate">{mission.title}</span>
                </button>
              </li>
            ))}
            {missions.length === 0 && (
              <li className="px-3 py-2 text-xs text-[#554240] italic">No missions yet</li>
            )}
          </ul>
        </section>
      </nav>

      <div className="px-2 pt-4 border-t border-[#554240] opacity-20">
        <p className="label text-[10px]">La Passione Inc. &copy; 2026</p>
      </div>
    </aside>
  );
};

const SidebarItem: React.FC<{ icon: React.ReactNode; label: string; active?: boolean }> = ({ icon, label, active }) => (
  <li>
    <button className={clsx(
      "w-full flex items-center gap-3 px-3 py-2 rounded-sm text-sm transition-colors",
      active ? "text-[#ffb3b5]" : "text-[#9ca3af] hover:bg-[#2a2a2a] hover:text-white"
    )}>
      <span className={clsx(active ? "text-[#ffb3b5]" : "opacity-60")}>{icon}</span>
      <span>{label}</span>
    </button>
  </li>
);
