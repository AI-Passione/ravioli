import { describe, it, expect, beforeEach } from 'vitest';
import { renderSidebar } from '../../../src/ravioli/frontend/src/components/Sidebar';
import { store } from '../../../src/ravioli/frontend/src/store';

describe('Sidebar Component', () => {
  beforeEach(() => {
    store.setAnalyses([{ id: 'a1', title: 'Test Analysis', status: 'idle', created_at: '', updated_at: '' }]);
    store.setActiveAnalysisId('a1');
  });

  it('should render the analysis title', () => {
    const sidebar = renderSidebar();
    expect(sidebar.innerHTML).toContain('Test Analysis');
  });

  it('should highlight the active analysis', () => {
    const sidebar = renderSidebar();
    const activeBtn = sidebar.querySelector('[data-analysis-id="a1"].active');
    expect(activeBtn?.textContent).toContain('Test Analysis');
  });

  it('should render the system labels', () => {
    const sidebar = renderSidebar();
    expect(sidebar.innerHTML).toContain('Vibe Analytics');
    expect(sidebar.innerHTML).toContain('Insights');
    expect(sidebar.innerHTML).toContain('Knowledge');
    expect(sidebar.innerHTML).toContain('Data');
    expect(sidebar.innerHTML).toContain('Governance');
    expect(sidebar.innerHTML).toContain('Settings');
    expect(sidebar.innerHTML).toContain('Historical Analyses');
  });

  it('should show "No Analyses found" when the list is empty', () => {
    store.setAnalyses([]);
    const sidebar = renderSidebar();
    expect(sidebar.innerHTML).toContain('No Analyses found');
  });

  it('should highlight the active view', () => {
    store.setCurrentView('governance');
    const sidebar = renderSidebar();
    const govBtn = sidebar.querySelector('[data-nav="governance"]');
    expect(govBtn?.classList.contains('active')).toBe(true);
  });

  it('should update the store when a nav item is clicked', () => {
    const sidebar = renderSidebar();
    const settingsBtn = sidebar.querySelector('[data-nav="settings"]') as HTMLButtonElement;
    settingsBtn?.click();
    expect(store.getCurrentView()).toBe('settings');
  });

  it('should render different icons for quick insights vs deep dives', () => {
    store.setAnalyses([
      { 
        id: 'q1', 
        title: 'Quick', 
        status: 'completed', 
        analysis_metadata: { type: 'quick_insight' },
        created_at: '', 
        updated_at: '' 
      },
      { 
        id: 'd1', 
        title: 'Deep', 
        status: 'completed', 
        analysis_metadata: { type: 'deep_dive' },
        created_at: '', 
        updated_at: '' 
      }
    ]);
    const sidebar = renderSidebar();
    
    const quickIcon = sidebar.querySelector('[data-analysis-id="q1"] [data-icon]');
    const deepIcon = sidebar.querySelector('[data-analysis-id="d1"] [data-icon]');
    
    expect(quickIcon?.textContent).toBe('bolt');
    expect(deepIcon?.textContent).toBe('terminal');
  });
});
