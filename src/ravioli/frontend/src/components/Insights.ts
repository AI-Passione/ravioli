import { api } from '../services/api';
import { formatDistanceToNow, format } from 'date-fns';
import type { Insight, InsightStats, InsightsSummary } from '../types';

const DAY_OPTIONS = [1, 3, 7, 14, 28, 30];

// Module-level state so re-renders within the same session preserve selections
let activeDays = 7;
let summaryCache: Map<number, InsightsSummary> = new Map();
export const clearInsightsCache = () => summaryCache.clear();

function banCard(value: number | string, label: string, icon: string, accent = 'text-primary') {
  return `
    <div class="glass-card px-6 py-5 rounded-2xl flex items-center gap-5 group cursor-default">
      <div class="w-12 h-12 rounded-xl bg-surface-container-high flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
        <span class="material-symbols-outlined ${accent} text-2xl shrink-0" data-icon="${icon}">${icon}</span>
      </div>
      <div class="flex flex-col gap-0.5 min-w-0">
        <span class="text-[10px] uppercase tracking-[0.3em] text-outline font-label-sm opacity-50 truncate">${label}</span>
        <span class="font-display-lg text-3xl text-on-surface tracking-tighter tabular-nums leading-none">${value}</span>
      </div>
    </div>`;
}

function insightPill(insight: Insight, context: 'queue' | 'feed') {
  const ago = formatDistanceToNow(new Date(insight.created_at), { addSuffix: true });
  const dateStr = format(new Date(insight.created_at), 'MMM d');
  const source = insight.source_label ?? 'Unknown analysis';

  if (context === 'queue') {
    return `
      <div class="review-item flex items-start gap-4 p-5 rounded-2xl bg-surface-container-low/30 border border-white/5 hover:border-tertiary/30 transition-all duration-500 group insight-card-hover" data-insight-id="${insight.id}">
        <div class="w-2 h-2 rounded-full bg-tertiary mt-2 shrink-0 animate-pulse shadow-[0_0_8px_rgba(var(--tertiary-rgb),0.5)]"></div>
        <div class="flex-1 min-w-0 space-y-2">
          <p class="text-sm font-body-md text-on-surface leading-relaxed group-hover:text-white transition-colors">${insight.content}</p>
          <div class="flex items-center gap-3">
            <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm opacity-40">${source}</span>
            <span class="text-[10px] text-outline opacity-20">·</span>
            <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm opacity-40">${ago}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
          <button class="btn-verify-insight flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary/10 text-primary border border-primary/20 hover:bg-primary hover:text-on-primary transition-all text-[10px] uppercase tracking-widest font-bold" data-id="${insight.id}">
            <span class="material-symbols-outlined text-sm" data-icon="check">check</span>
            Verify
          </button>
          <button class="btn-reject-insight p-2 rounded-full bg-error/5 text-outline hover:text-error hover:bg-error/10 border border-transparent hover:border-error/20 transition-all" data-id="${insight.id}" title="Reject">
            <span class="material-symbols-outlined text-sm" data-icon="close">close</span>
          </button>
        </div>
      </div>`;
  }

  return `
    <div class="flex items-start gap-5 py-6 border-b border-white/5 last:border-0 group insight-card-hover rounded-xl px-4 -mx-4 transition-all duration-500">
      <div class="flex flex-col items-center gap-1 shrink-0 w-12 text-center">
        <span class="text-xl font-display-lg text-primary tabular-nums group-hover:scale-110 transition-transform duration-500">${dateStr.split(' ')[1]}</span>
        <span class="text-[9px] uppercase tracking-[0.2em] text-outline opacity-40 font-bold">${dateStr.split(' ')[0]}</span>
      </div>
      <div class="flex-1 min-w-0 space-y-2">
        <p class="text-sm font-body-md text-on-surface-variant leading-relaxed group-hover:text-white transition-colors duration-500">${insight.content}</p>
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-xs opacity-50 group-hover:opacity-100 transition-opacity" data-icon="verified">verified</span>
          <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm opacity-30 group-hover:opacity-60 transition-opacity">${source}</span>
          <span class="text-[10px] text-outline opacity-20">·</span>
          <span class="text-[10px] uppercase tracking-[0.2em] text-outline font-label-sm opacity-30 group-hover:opacity-60 transition-opacity">${ago}</span>
        </div>
      </div>
    </div>`;
}

export function renderInsights() {
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 overflow-y-auto bg-background h-screen flex flex-col custom-scrollbar';

  // Render with loading skeletons, then hydrate async
  container.innerHTML = `
    <!-- Page Header -->
    <header class="px-12 pt-12 pb-8 shrink-0 animate-reveal">
      <div class="space-y-2">
        <p class="text-[10px] uppercase tracking-[0.3em] text-primary-fixed-dim opacity-60 font-label-sm">Studio Noir</p>
        <h1 class="font-display-lg text-4xl text-on-surface tracking-tight">Insights</h1>
        <p class="text-sm text-on-surface-variant font-body-md opacity-60">Distilled intelligence from your verified analyses.</p>
      </div>
      <div class="mt-8 h-px bg-gradient-to-r from-primary/20 via-outline-variant/20 to-transparent"></div>
    </header>

    <div class="flex-1 px-12 pb-16 space-y-16">

      <!-- BANs -->
      <section id="bans-section">
        <div class="grid grid-cols-3 gap-4">
          <div class="rounded-2xl animate-pulse bg-surface-container-low h-16"></div>
          <div class="rounded-2xl animate-pulse bg-surface-container-low h-16"></div>
          <div class="rounded-2xl animate-pulse bg-surface-container-low h-16"></div>
        </div>
      </section>

      <!-- Hero: AI Summary (dominant) -->
      <section id="hero-section" class="relative">
        <div class="flex items-center justify-between mb-8">
          <div class="flex items-center gap-5">
            <div class="w-14 h-14 rounded-[1.25rem] bg-primary/10 flex items-center justify-center border border-primary/20 shadow-lg shadow-primary/5 animate-float">
              <span class="material-symbols-outlined text-primary text-3xl glow-primary" data-icon="auto_awesome">auto_awesome</span>
            </div>
            <div>
              <h2 class="text-2xl font-headline-sm text-on-surface uppercase tracking-[0.2em] font-medium">Intelligence Brief</h2>
              <div class="flex items-center gap-2 mt-1">
                <span class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                <p class="text-[10px] uppercase tracking-[0.3em] text-primary-fixed-dim opacity-40 font-bold">Synthesized Analytics</p>
              </div>
            </div>
          </div>
          <!-- Day selector -->
          <div class="flex items-center gap-1 p-1.5 bg-surface-container-low/50 backdrop-blur-md rounded-full border border-white/5" id="day-selector">
            ${DAY_OPTIONS.map(d => `
              <button class="day-btn px-4 py-2 rounded-full text-[10px] font-bold uppercase tracking-[0.15em] transition-all duration-500 ${d === activeDays ? 'bg-primary text-on-primary shadow-lg shadow-primary/20' : 'text-outline hover:text-white hover:bg-white/5'}" data-days="${d}">${d}d</button>
            `).join('')}
          </div>
        </div>
        
        <div id="hero-content" class="glass-card p-12 rounded-[2.5rem] relative overflow-hidden group">
          <!-- Animated Background Elements -->
          <div class="absolute -top-24 -right-24 w-96 h-96 bg-primary/5 rounded-full blur-[120px] pointer-events-none group-hover:bg-primary/10 transition-colors duration-1000"></div>
          <div class="absolute -bottom-16 -left-16 w-64 h-64 bg-tertiary/5 rounded-full blur-[100px] pointer-events-none group-hover:bg-tertiary/10 transition-colors duration-1000"></div>
          <div class="absolute inset-0 bg-noise opacity-[0.02] pointer-events-none"></div>
          
          <div id="hero-text" class="relative z-10 min-h-[160px] flex flex-col justify-center">
            <div class="flex flex-col items-center gap-4 py-8 opacity-40">
              <span class="material-symbols-outlined text-4xl animate-spin" data-icon="progress_activity">progress_activity</span>
              <span class="text-xs uppercase tracking-[0.3em] font-bold">Initializing intelligence core…</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Two-column: Review Queue + News Feed -->
      <div class="grid grid-cols-2 gap-10">

        <!-- Review Queue -->
        <section>
          <div class="flex items-center gap-3 mb-6">
            <div class="w-8 h-8 rounded-xl bg-tertiary/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-tertiary" data-icon="pending_actions">pending_actions</span>
            </div>
            <h2 class="text-lg font-headline-sm text-on-surface uppercase tracking-[0.15em]">Review Queue</h2>
            <span id="queue-badge" class="ml-auto px-2 py-0.5 rounded-full bg-tertiary/10 text-tertiary text-[10px] font-label-sm uppercase tracking-widest hidden">0</span>
          </div>
          <div id="review-queue" class="space-y-3">
            <div class="h-20 rounded-2xl bg-surface-container-low animate-pulse"></div>
            <div class="h-20 rounded-2xl bg-surface-container-low animate-pulse"></div>
          </div>
        </section>

        <!-- News Feed -->
        <section>
          <div class="flex items-center gap-3 mb-6">
            <div class="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary" data-icon="newspaper">newspaper</span>
            </div>
            <h2 class="text-lg font-headline-sm text-on-surface uppercase tracking-[0.15em]">News Feed</h2>
          </div>
          <div id="news-feed" class="space-y-0">
            <div class="h-16 border-b border-outline-variant/10 animate-pulse bg-surface-container-low/20 rounded mb-1"></div>
            <div class="h-16 border-b border-outline-variant/10 animate-pulse bg-surface-container-low/20 rounded mb-1"></div>
            <div class="h-16 border-b border-outline-variant/10 animate-pulse bg-surface-container-low/20 rounded"></div>
          </div>
        </section>

      </div>
    </div>
  `;

  // Hydrate all sections in parallel
  hydrate(container);

  return container;
}

async function hydrate(container: HTMLElement) {
  await Promise.all([
    hydrateBans(container),
    hydrateSummary(container, activeDays),
    hydrateQueue(container),
    hydrateFeed(container),
  ]);

  // Day selector interaction
  container.querySelectorAll('.day-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const days = parseInt(btn.getAttribute('data-days') || '7');
      activeDays = days;
      container.querySelectorAll('.day-btn').forEach(b => {
        b.classList.toggle('bg-primary', b === btn);
        b.classList.toggle('text-on-primary', b === btn);
        b.classList.toggle('text-outline', b !== btn);
      });
      await hydrateSummary(container, days);
    });
  });
}

async function hydrateBans(container: HTMLElement) {
  const section = container.querySelector('#bans-section');
  if (!section) return;
  try {
    const stats = await api.getInsightStats();
    section.innerHTML = `
      <div class="grid grid-cols-3 gap-6">
        <div class="opacity-0 animate-reveal stagger-1">${banCard(stats.verified_count, 'Verified Insights', 'verified', 'text-primary')}</div>
        <div class="opacity-0 animate-reveal stagger-2">${banCard(stats.analyses_count, 'Total Analyses', 'analytics', 'text-secondary')}</div>
        <div class="opacity-0 animate-reveal stagger-3">${banCard(stats.contributors_count, 'Insight Contributors', 'group', 'text-tertiary')}</div>
      </div>`;
  } catch {
    section.innerHTML = `<p class="text-sm text-outline opacity-50">Failed to load stats.</p>`;
  }
}

async function hydrateSummary(container: HTMLElement, days: number) {
  const heroText = container.querySelector('#hero-text');
  if (!heroText) return;

  heroText.innerHTML = `
    <div class="flex items-center gap-3 opacity-40">
      <span class="material-symbols-outlined animate-spin" data-icon="progress_activity">progress_activity</span>
      <span class="text-sm uppercase tracking-widest font-label-sm">Synthesizing ${days}d intelligence…</span>
    </div>`;

  try {
    // Use cache to avoid re-fetching same window
    let data = summaryCache.get(days);
    if (!data) {
      data = await api.getInsightsSummary(days);
      summaryCache.set(days, data);
    }
    // Parse bullet lines from the summary; fall back to treating full text as one bullet
    const allBullets = data.summary
      .split('\n')
      .map(l => l.replace(/^[\s\-*•]+/, '').trim())
      .filter(l => l.length > 10);

    const isExpandable = allBullets.length > 4;
    const bullets = isExpandable ? allBullets.slice(0, 4) : allBullets;
    const hiddenBullets = isExpandable ? allBullets.slice(4) : [];

    const renderBullet = (b: string, index: number) => `
      <li class="flex items-start gap-5 group/item opacity-0 animate-reveal" style="animation-delay: ${index * 0.1}s">
        <div class="mt-[0.65em] shrink-0 w-2 h-2 rounded-full bg-primary/40 group-hover/item:bg-primary group-hover/item:scale-125 transition-all duration-300 shadow-[0_0_8px_rgba(var(--primary-rgb),0.3)]"></div>
        <span class="text-lg font-body-lg text-on-surface-variant leading-relaxed group-hover/item:text-on-surface transition-colors duration-300">${b}</span>
      </li>`;

    const bulletHtml = bullets.length > 0
      ? bullets.map((b, i) => renderBullet(b, i)).join('')
      : `<li class="text-on-surface-variant opacity-60 font-body-md text-sm">${data.summary}</li>`;

    const countNote = data.insight_count > 0
      ? `<div class="pt-8 border-t border-white/5 flex items-center justify-between mt-10">
          <div class="flex items-center gap-3 opacity-30">
            <span class="material-symbols-outlined text-base" data-icon="data_exploration">data_exploration</span>
            <span class="text-[10px] uppercase tracking-[0.3em] font-bold">${data.insight_count} verified signal${data.insight_count !== 1 ? 's' : ''} ingested</span>
          </div>
          <button id="btn-copy-brief" class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/5 text-[10px] uppercase tracking-[0.2em] text-outline hover:text-primary transition-all font-bold group/copy">
            <span class="material-symbols-outlined text-sm group-hover/copy:scale-110 transition-transform" data-icon="content_copy">content_copy</span>
            <span>Copy Brief</span>
          </button>
        </div>`
      : '';

    heroText.innerHTML = `
      <ul id="hero-bullets" class="space-y-6 list-none">${bulletHtml}</ul>
      ${isExpandable ? `
        <div id="hidden-bullets" class="hidden space-y-6 mt-6 animate-in fade-in slide-in-from-top-4 duration-500">
          ${hiddenBullets.map(renderBullet).join('')}
        </div>
        <button id="btn-toggle-hero" class="mt-10 flex items-center gap-2.5 text-[10px] uppercase tracking-[0.25em] text-primary hover:text-primary-fixed transition-all font-bold group">
          <div class="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
            <span class="material-symbols-outlined text-xs group-hover:translate-y-0.5 transition-transform" data-icon="expand_more">expand_more</span>
          </div>
          <span>Explore Full Intelligence</span>
        </button>
      ` : ''}
      ${countNote}`;

    // Handle Copy
    heroText.querySelector('#btn-copy-brief')?.addEventListener('click', () => {
      navigator.clipboard.writeText(allBullets.join('\n'));
      const btn = heroText.querySelector('#btn-copy-brief');
      if (btn) {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<span class="material-symbols-outlined text-sm text-primary" data-icon="done">done</span><span class="text-primary">Copied!</span>`;
        setTimeout(() => { btn.innerHTML = originalHtml; }, 2000);
      }
    });

    if (isExpandable) {
      const toggleBtn = heroText.querySelector('#btn-toggle-hero');
      const hiddenEl = heroText.querySelector('#hidden-bullets');
      toggleBtn?.addEventListener('click', () => {
        const isHidden = hiddenEl?.classList.contains('hidden');
        hiddenEl?.classList.toggle('hidden');
        if (toggleBtn) {
          toggleBtn.innerHTML = isHidden 
            ? `<span class="material-symbols-outlined text-sm group-hover:-translate-y-0.5 transition-transform" data-icon="expand_less">expand_less</span><span>Collapse Brief</span>`
            : `<span class="material-symbols-outlined text-sm group-hover:translate-y-0.5 transition-transform" data-icon="expand_more">expand_more</span><span>Expand Brief</span>`;
        }
      });
    }
  } catch {
    heroText.innerHTML = `<p class="text-sm text-outline opacity-50">Summary unavailable.</p>`;
  }
}

async function hydrateQueue(container: HTMLElement) {
  const queueEl = container.querySelector('#review-queue');
  const badge = container.querySelector('#queue-badge');
  if (!queueEl) return;
  try {
    let queue = await api.getReviewQueue();

    const render = (items: typeof queue) => {
      if (badge) {
        if (items.length > 0) {
          badge.textContent = String(items.length);
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      }
      queueEl.innerHTML = items.length === 0
        ? `<div class="glass-card flex flex-col items-center gap-4 py-16 text-center rounded-[2rem] border-dashed border-white/5 group animate-reveal">
            <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-700">
              <span class="material-symbols-outlined text-4xl text-outline opacity-20" data-icon="inbox_customize">inbox_customize</span>
            </div>
            <div class="space-y-1">
              <p class="text-xs uppercase tracking-[0.3em] font-bold text-on-surface opacity-40">Queue is Clear</p>
              <p class="text-[10px] uppercase tracking-[0.1em] text-outline opacity-20 font-medium">All insights have been processed</p>
            </div>
          </div>`
        : items.map((i, index) => `<div class="opacity-0 animate-reveal" style="animation-delay: ${index * 0.05}s">${insightPill(i, 'queue')}</div>`).join('');

      // Bind verify / reject buttons
      queueEl.querySelectorAll('.btn-verify-insight').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          if (!id) return;
          btn.setAttribute('disabled', 'true');
          try {
            await api.verifyInsight(id);
            queue = queue.filter(i => i.id !== id);
            summaryCache.clear(); // Invalidate summary cache
            render(queue);
            // Refresh feed and BANs
            await Promise.all([hydrateFeed(container), hydrateBans(container), hydrateSummary(container, activeDays)]);
          } catch { btn.removeAttribute('disabled'); }
        });
      });

      queueEl.querySelectorAll('.btn-reject-insight').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          if (!id) return;
          try {
            await api.rejectInsight(id);
            queue = queue.filter(i => i.id !== id);
            render(queue);
            await hydrateBans(container);
          } catch {}
        });
      });
    };

    render(queue);
  } catch {
    queueEl.innerHTML = `<p class="text-sm text-outline opacity-50">Failed to load queue.</p>`;
  }
}

async function hydrateFeed(container: HTMLElement) {
  const feedEl = container.querySelector('#news-feed');
  if (!feedEl) return;
  try {
    const feed = await api.getInsightsFeed(activeDays <= 7 ? 30 : activeDays);
    feedEl.innerHTML = feed.length === 0
      ? `<div class="glass-card flex flex-col items-center gap-4 py-16 text-center rounded-[2rem] border-dashed border-white/5 group animate-reveal">
          <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform duration-700">
            <span class="material-symbols-outlined text-4xl text-outline opacity-20" data-icon="newspaper">newspaper</span>
          </div>
          <div class="space-y-1">
            <p class="text-xs uppercase tracking-[0.3em] font-bold text-on-surface opacity-40">No Activity</p>
            <p class="text-[10px] uppercase tracking-[0.1em] text-outline opacity-20 font-medium">Verified signals will appear here</p>
          </div>
        </div>`
      : feed.map((i, index) => `<div class="opacity-0 animate-reveal" style="animation-delay: ${index * 0.05}s">${insightPill(i, 'feed')}</div>`).join('');
  } catch {
    feedEl.innerHTML = `<p class="text-sm text-outline opacity-50">Failed to load feed.</p>`;
  }
}
