import { describe, it, expect, beforeEach } from 'vitest';
import { renderSidebar } from '../../../src/ravioli/frontend/src/components/Sidebar';
import { store } from '../../../src/ravioli/frontend/src/store';

describe('Sidebar Component', () => {
  beforeEach(() => {
    store.setMissions([{ id: 'm1', title: 'Test Mission', status: 'idle', created_at: '', updated_at: '' }]);
    store.setActiveMissionId('m1');
  });

  it('should render the mission title', () => {
    const sidebar = renderSidebar();
    expect(sidebar.innerHTML).toContain('Test Mission');
  });

  it('should highlight the active mission', () => {
    const sidebar = renderSidebar();
    const activeBtn = sidebar.querySelector('[data-mission-id="m1"].active');
    expect(activeBtn?.textContent).toContain('Test Mission');
  });

  it('should render the system labels', () => {
    const sidebar = renderSidebar();
    expect(sidebar.innerHTML).toContain('System');
    expect(sidebar.innerHTML).toContain('Investigations');
  });
});
