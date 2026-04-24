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
    expect(sidebar.innerHTML).toContain('Investigations');
  });
});
