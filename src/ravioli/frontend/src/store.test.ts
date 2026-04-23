import { describe, it, expect, beforeEach } from 'vitest';
import { store } from './store';

describe('Store', () => {
  beforeEach(() => {
    store.setMissions([]);
    store.setActiveMissionId(undefined);
    store.setLogs([]);
  });

  it('should set and get missions', () => {
    const mockMissions = [{ id: '1', title: 'Test', status: 'idle', created_at: '', updated_at: '' }];
    store.setMissions(mockMissions);
    expect(store.getMissions()).toEqual(mockMissions);
  });

  it('should update active mission id', () => {
    store.setActiveMissionId('42');
    expect(store.getActiveMissionId()).toBe('42');
  });

  it('should notify listeners on change', () => {
    let called = false;
    store.subscribe(() => { called = true; });
    store.setActiveMissionId('1');
    expect(called).toBe(true);
  });
});
