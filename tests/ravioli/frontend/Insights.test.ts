import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderInsights, clearInsightsCache } from '../../../src/ravioli/frontend/src/components/Insights';
import { api } from '../../../src/ravioli/frontend/src/services/api';

vi.mock('../../../src/ravioli/frontend/src/services/api', () => ({
  api: {
    getInsightStats: vi.fn(),
    getInsightsSummary: vi.fn(),
    getReviewQueue: vi.fn(),
    getInsightsFeed: vi.fn(),
  }
}));

describe('Insights Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearInsightsCache();
    
    // Default mocks
    (api.getInsightStats as any).mockResolvedValue({ verified_count: 5, analyses_count: 10, contributors_count: 3 });
    (api.getInsightsSummary as any).mockResolvedValue({ summary: 'One exceeds 10 chars\nTwo exceeds 10 chars\nThree exceeds 10 chars', insight_count: 3, days: 7 });
    (api.getReviewQueue as any).mockResolvedValue([]);
    (api.getInsightsFeed as any).mockResolvedValue([]);

    // Mock scrollTo
    vi.stubGlobal('scrollTo', vi.fn());
  });

  it('should render the Insights heading', async () => {
    const el = renderInsights();
    expect(el.innerHTML).toContain('Insights');
  });

  it('should render Intelligence Brief section', async () => {
    const el = renderInsights();
    expect(el.innerHTML).toContain('Intelligence Brief');
  });

  it('should render BANs with mocked stats', async () => {
    const el = renderInsights();
    await new Promise(resolve => setTimeout(resolve, 50));
    
    expect(el.innerHTML).toContain('5');
    expect(el.innerHTML).toContain('Verified Insights');
  });

  describe('Expandable Summary', () => {
    it('should NOT show toggle when summary has <= 4 points', async () => {
      (api.getInsightsSummary as any).mockResolvedValue({ 
        summary: '• Point 1 exceeds 10 chars\n• Point 2 exceeds 10 chars\n• Point 3 exceeds 10 chars\n• Point 4 exceeds 10 chars', 
        insight_count: 4, 
        days: 7 
      });

      const el = renderInsights();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      expect(el.innerHTML).toContain('Point 4');
      expect(el.querySelector('#btn-toggle-hero')).toBeNull();
    });

    it('should show toggle when summary has > 4 points', async () => {
      (api.getInsightsSummary as any).mockResolvedValue({ 
        summary: '• Point 1 exceeds 10 chars\n• Point 2 exceeds 10 chars\n• Point 3 exceeds 10 chars\n• Point 4 exceeds 10 chars\n• Point 5 exceeds 10 chars', 
        insight_count: 5, 
        days: 7 
      });

      const el = renderInsights();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const toggleBtn = el.querySelector('#btn-toggle-hero');
      expect(toggleBtn).not.toBeNull();
      expect(toggleBtn?.textContent).toContain('Explore Full Intelligence');
      
      const hiddenContainer = el.querySelector('#hidden-bullets');
      expect(hiddenContainer?.classList.contains('hidden')).toBe(true);
      expect(hiddenContainer?.innerHTML).toContain('Point 5');
    });

    it('should toggle visibility when clicking the button', async () => {
      (api.getInsightsSummary as any).mockResolvedValue({ 
        summary: '• Point 1 exceeds 10 chars\n• Point 2 exceeds 10 chars\n• Point 3 exceeds 10 chars\n• Point 4 exceeds 10 chars\n• Point 5 exceeds 10 chars', 
        insight_count: 5, 
        days: 7 
      });

      const el = renderInsights();
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const toggleBtn = el.querySelector('#btn-toggle-hero') as HTMLButtonElement;
      const hiddenContainer = el.querySelector('#hidden-bullets') as HTMLElement;
      
      expect(hiddenContainer.classList.contains('hidden')).toBe(true);
      
      toggleBtn.click();
      expect(hiddenContainer.classList.contains('hidden')).toBe(false);
      expect(toggleBtn.textContent).toContain('Collapse Brief');
      
      toggleBtn.click();
      expect(hiddenContainer.classList.contains('hidden')).toBe(true);
      expect(toggleBtn.textContent).toContain('Expand Brief');
    });
  });
});
