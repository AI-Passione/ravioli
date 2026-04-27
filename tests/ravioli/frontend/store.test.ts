import { describe, it, expect, beforeEach } from 'vitest';
import { store } from '../../../src/ravioli/frontend/src/store';

describe('Store', () => {
  beforeEach(() => {
    store.setAnalyses([]);
    store.setActiveAnalysisId(undefined);
    store.setLogs([]);
  });

  it('should set and get analyses', () => {
    const mockAnalyses = [{ id: '1', title: 'Test', status: 'idle', created_at: '', updated_at: '' }];
    store.setAnalyses(mockAnalyses);
    expect(store.getAnalyses()).toEqual(mockAnalyses);
  });

  it('should update active analysis id', () => {
    store.setActiveAnalysisId('42');
    expect(store.getActiveAnalysisId()).toBe('42');
  });

  it('should notify listeners on change', () => {
    let called = false;
    store.subscribe(() => { called = true; });
    store.setActiveAnalysisId('1');
    expect(called).toBe(true);
  });

  it('should manage current view and clear active analysis when switching to main views', () => {
    store.setActiveAnalysisId('42');
    store.setCurrentView('governance');
    expect(store.getCurrentView()).toBe('governance');
    expect(store.getActiveAnalysisId()).toBeUndefined();
  });

  it('should set active analysis id and switch view to dashboard', () => {
    store.setCurrentView('insights');
    store.setActiveAnalysisId('123');
    expect(store.getCurrentView()).toBe('dashboard');
    expect(store.getActiveAnalysisId()).toBe('123');
  });
});
