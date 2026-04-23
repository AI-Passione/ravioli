import React from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Shell } from './components/layout/Shell';
import { Notebook } from './components/notebook/Notebook';
import { api } from './services/api';
import type { Mission } from './types';

function App() {
  const [missions, setMissions] = React.useState<Mission[]>([]);
  const [activeMissionId, setActiveMissionId] = React.useState<string | undefined>();
  const [logs, setLogs] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  // Initial load: Fetch missions
  React.useEffect(() => {
    const loadMissions = async () => {
      try {
        const data = await api.listMissions();
        setMissions(data);
        if (data.length > 0 && !activeMissionId) {
          setActiveMissionId(data[0].id);
        }
      } catch (err) {
        console.error('Failed to load missions', err);
      } finally {
        setLoading(false);
      }
    };
    loadMissions();
  }, []);

  // Poll for logs when mission is active
  React.useEffect(() => {
    if (!activeMissionId) return;

    const fetchLogs = async () => {
      try {
        const data = await api.listLogs(activeMissionId);
        // Map backend logs to UI format
        const uiLogs = data.map(l => ({
          id: l.id,
          type: l.log_type === 'user_query' ? 'user' : 'agent',
          content: l.content,
          status: 'completed'
        }));
        setLogs(uiLogs);
      } catch (err) {
        console.error('Failed to load logs', err);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [activeMissionId]);

  const handleCreateMission = async () => {
    try {
      const title = prompt('Mission Title:');
      if (!title) return;
      const newMission = await api.createMission({ title });
      setMissions([newMission, ...missions]);
      setActiveMissionId(newMission.id);
      setLogs([]);
    } catch (err) {
      alert('Failed to create mission');
    }
  };

  const handleExecuteCell = async (_cellId: string, value: string) => {
    if (!activeMissionId) return;
    try {
      await api.askQuestion(activeMissionId, value);
      // Logs will be updated by the poller
    } catch (err) {
      alert('Failed to submit question');
    }
  };

  const handleAddCell = () => {
    setLogs([
      ...logs,
      {
        id: 'new-' + Date.now(),
        type: 'user',
        content: '',
        status: 'idle'
      }
    ]);
  };

  const activeMission = missions.find(m => m.id === activeMissionId);

  return (
    <Shell
      sidebar={
        <Sidebar
          activeMissionId={activeMissionId}
          missions={missions}
          onSelectMission={setActiveMissionId}
          onCreateMission={handleCreateMission}
        />
      }
    >
      {loading ? (
        <div className="flex items-center justify-center h-full">
          <div className="label animate-pulse">Initializing Systems...</div>
        </div>
      ) : activeMission ? (
        <Notebook
          missionTitle={activeMission.title}
          logs={logs}
          onExecuteCell={handleExecuteCell}
          onAddCell={handleAddCell}
        />
      ) : (
        <div className="flex flex-col items-center justify-center h-[60vh] text-[#a38b88]">
          <h2 className="text-2xl mb-4 font-display">Select a Mission to Begin</h2>
          <p className="label opacity-60">The Silent Concierge is waiting.</p>
        </div>
      )}
    </Shell>
  );
}

export default App;
