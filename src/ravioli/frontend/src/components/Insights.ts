import { store } from '../store';
import MarkdownIt from 'markdown-it';
import { formatDistanceToNow } from 'date-fns';

const md = new MarkdownIt({ html: false, linkify: true, typographer: true });

function excerpt(markdown: string, maxChars = 280): string {
  const plain = markdown
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .replace(/^>\s?.*/gm, '')
    .replace(/\n{2,}/g, ' ')
    .trim();
  return plain.length > maxChars ? plain.slice(0, maxChars) + '…' : plain;
}

export function renderInsights() {
  const analyses = store.getAnalyses();
  const approved = analyses.filter(a => a.analysis_metadata?.is_approved && a.result);

  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 overflow-y-auto bg-background h-screen flex flex-col custom-scrollbar';

  const emptyState = `
    <div class="h-full w-full flex flex-col items-center justify-center relative z-10 px-margin">
      <div class="w-px h-24 bg-gradient-to-b from-transparent via-tertiary/30 to-transparent mb-scale-16"></div>
      <h1 class="font-display-lg text-display-lg text-on-surface mb-4 tracking-tight">No Insights Yet</h1>
      <p class="font-label-sm text-label-sm tracking-[0.4em] text-tertiary-fixed-dim uppercase">Run an analysis and approve its result to see it here.</p>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none"></div>
    </div>
  `;

  const cardGrid = approved.map(a => {
    const isQuick = a.analysis_metadata?.type === 'quick_insight';
    const icon = isQuick ? 'bolt' : 'terminal';
    const ago = formatDistanceToNow(new Date(a.updated_at), { addSuffix: true });
    const snippet = excerpt(a.result!);
    const followups: string[] = a.analysis_metadata?.followup_questions ?? [];

    return `
      <article
        class="insight-card glass-panel p-8 rounded-[1.5rem] flex flex-col gap-6 border-outline-variant/10 hover:border-primary/20 transition-all duration-500 cursor-pointer group animate-in fade-in slide-in-from-bottom-4 duration-700"
        data-analysis-id="${a.id}"
      >
        <!-- Header -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 transition-colors">
              <span class="material-symbols-outlined text-primary text-lg" data-icon="${icon}">${icon}</span>
            </div>
            <div>
              <h3 class="font-headline-sm text-on-surface text-base leading-tight group-hover:text-primary transition-colors">${a.title}</h3>
              <span class="text-[10px] uppercase tracking-widest text-outline font-label-sm opacity-60">${ago}</span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <span class="material-symbols-outlined text-primary text-lg" data-icon="arrow_forward">arrow_forward</span>
          </div>
        </div>

        <!-- Excerpt -->
        <p class="font-body-md text-on-surface-variant text-sm leading-relaxed line-clamp-4">${snippet}</p>

        <!-- Follow-up tags -->
        ${followups.length > 0 ? `
          <div class="flex flex-wrap gap-2 pt-2 border-t border-outline-variant/10">
            ${followups.slice(0, 2).map(q => `
              <span class="px-3 py-1 text-[10px] font-label-sm uppercase tracking-widest text-tertiary bg-tertiary/5 border border-tertiary/10 rounded-full truncate max-w-[220px]">${q}</span>
            `).join('')}
            ${followups.length > 2 ? `<span class="px-3 py-1 text-[10px] font-label-sm uppercase tracking-widest text-outline bg-surface-container-low rounded-full">+${followups.length - 2} more</span>` : ''}
          </div>
        ` : ''}

        <!-- Footer badge -->
        <div class="flex items-center gap-2 text-tertiary opacity-60">
          <span class="material-symbols-outlined text-sm" data-icon="check_circle">check_circle</span>
          <span class="text-[10px] uppercase tracking-widest font-label-sm">Approved Insight</span>
        </div>
      </article>
    `;
  }).join('');

  container.innerHTML = `
    <!-- Header -->
    <header class="px-12 pt-12 pb-8 shrink-0">
      <div class="flex items-end justify-between">
        <div class="space-y-2">
          <p class="text-[10px] uppercase tracking-[0.3em] text-primary-fixed-dim opacity-60 font-label-sm">Studio Noir</p>
          <h1 class="font-display-lg text-4xl text-on-surface tracking-tight">Insights</h1>
          <p class="text-sm text-on-surface-variant font-body-md opacity-70">
            ${approved.length === 0
              ? 'Approved findings from your analyses will appear here.'
              : `${approved.length} approved insight${approved.length !== 1 ? 's' : ''} distilled from your work.`}
          </p>
        </div>
        ${approved.length > 0 ? `
          <div class="flex items-center gap-2 px-4 py-2 bg-surface-container-lowest/50 backdrop-blur-md rounded-full border border-outline-variant/10">
            <span class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
            <span class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest text-[10px]">${approved.length} Active</span>
          </div>
        ` : ''}
      </div>
      <div class="mt-8 h-px bg-gradient-to-r from-primary/20 via-outline-variant/20 to-transparent"></div>
    </header>

    <!-- Content -->
    <div class="flex-1 px-12 pb-12">
      ${approved.length === 0
        ? emptyState
        : `<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">${cardGrid}</div>`}
    </div>
  `;

  // Navigate to analysis when clicking a card
  container.querySelectorAll('.insight-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.getAttribute('data-analysis-id');
      if (id) store.setActiveAnalysisId(id);
    });
  });

  return container;
}
