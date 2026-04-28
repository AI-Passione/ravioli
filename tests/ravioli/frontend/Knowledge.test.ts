import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderKnowledge } from '../../../src/ravioli/frontend/src/components/Knowledge';
import { store } from '../../../src/ravioli/frontend/src/store';

vi.mock('../../../src/ravioli/frontend/src/services/api', () => ({
  api: {
    listKnowledgePages: vi.fn(),
    createKnowledgePage: vi.fn(),
    updateKnowledgePage: vi.fn(),
    deleteKnowledgePage: vi.fn(),
  }
}));

vi.mock('../../../src/ravioli/frontend/src/store', () => ({
  store: {
    getKnowledgePages: vi.fn(),
    setKnowledgePages: vi.fn(),
  }
}));

describe('Knowledge Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the Knowledge Base header', () => {
    (store.getKnowledgePages as any).mockReturnValue([]);
    const el = renderKnowledge();
    expect(el.innerHTML).toContain('Knowledge Base');
    expect(el.innerHTML).toContain('Codified domain intelligence');
  });

  it('should render empty state message when no pages are available', () => {
    (store.getKnowledgePages as any).mockReturnValue([]);
    const el = renderKnowledge();
    expect(el.innerHTML).toContain('No intelligence codified yet');
  });

  it('should render a list of knowledge cards when data exists in store', () => {
    (store.getKnowledgePages as any).mockReturnValue([
      {
        id: '123',
        title: 'Project Phoenix',
        properties: {},
        content: [{ type: 'paragraph', paragraph: { rich_text: [{ text: { content: 'Strategic goals for 2024' }, plain_text: 'Strategic goals for 2024' }] } }],
        icon: { type: 'emoji', emoji: '🔥' },
        cover: null,
        ownership_type: 'team',
        updated_at: '2024-01-01T12:00:00Z'
      }
    ]);
    
    const el = renderKnowledge();
    expect(el.innerHTML).toContain('Project Phoenix');
    expect(el.innerHTML).toContain('Strategic goals for 2024');
    expect(el.innerHTML).toContain('🔥');
    expect(el.innerHTML).toContain('team');
  });

  it('should escape HTML in titles to prevent XSS and reinterpretation errors', () => {
    (store.getKnowledgePages as any).mockReturnValue([
      {
        id: '456',
        title: '<script>alert("xss")</script>',
        properties: {},
        content: [{ type: 'paragraph', paragraph: { rich_text: [{ text: { content: 'Safe content' } }] } }],
        updated_at: '2024-01-01T12:00:00Z',
        ownership_type: 'individual'
      }
    ]);
    
    const el = renderKnowledge();
    expect(el.innerHTML).toContain('&lt;script&gt;alert("xss")&lt;/script&gt;');
    expect(el.innerHTML).not.toContain('<script>');
  });

  it('should display a fallback icon when no icon is provided', () => {
    (store.getKnowledgePages as any).mockReturnValue([
      {
        id: '789',
        title: 'Default Icon Page',
        properties: {},
        content: [],
        updated_at: '2024-01-01T12:00:00Z',
        ownership_type: 'individual'
      }
    ]);
    
    const el = renderKnowledge();
    expect(el.innerHTML).toContain('📄');
  });
});
