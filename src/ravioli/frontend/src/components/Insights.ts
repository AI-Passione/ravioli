import { store } from '../store';
import { api } from '../services/api';
import { formatDistanceToNow, format } from 'date-fns';
import type { Insight, InsightStats, InsightsSummary } from '../types';

const DAY_OPTIONS = [1, 3, 7, 14, 28, 30];

// Module-level state so re-renders within the same session preserve selections
let activeDays = 7;
let summaryCache: Map<number, InsightsSummary> = new Map();

function banCard(value: number | string, label: string, icon: string, accent = 'text-primary') {
  return `
    <div class="glass-panel px-6 py-4 rounded-2xl flex items-center gap-5 border-outline-variant/10">
      <span class="material-symbols-outlined ${accent} text-xl shrink-0" data-icon="${icon}">${icon}</span>
      <div class="flex flex-col gap-0.5 min-w-0">
        <span class="text-[10px] uppercase tracking-[0.25em] text-outline font-label-sm opacity-60 truncate">${label}</span>
        <span class="font-display-lg text-3xl text-on-surface tracking-tight tabular-nums leading-none">${value}</span>
      </div>
    </div>`;
}

function insightPill(insight: Insight, context: 'queue' | 'feed') {
  const ago = formatDistanceToNow(new Date(insight.created_at), { addSuffix: true });
  const dateStr = format(new Date(insight.created_at), 'MMM d');
  const source = insight.source_label ?? 'Unknown analysis';

  if (context === 'queue') {
    return `
      <div class="review-item flex items-start gap-4 p-5 rounded-2xl bg-surface-container-low border border-outline-variant/10 hover:border-tertiary/20 transition-all duration-300 group" data-insight-id="${insight.id}">
        <div class="w-2 h-2 rounded-full bg-tertiary mt-2 shrink-0 animate-pulse"></div>
        <div class="flex-1 min-w-0 space-y-2">
          <p class="text-sm font-body-md text-on-surface leading-relaxed">${insight.content}</p>
          <div class="flex items-center gap-3">
            <span class="text-[10px] uppercase tracking-widest text-outline font-label-sm opacity-50">${source}</span>
            <span class="text-[10px] text-outline opacity-30">·</span>
            <span class="text-[10px] uppercase tracking-widest text-outline font-label-sm opacity-50">${ago}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          <button class="btn-verify-insight flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-primary/30 text-primary hover:bg-primary/10 transition-all text-[10px] uppercase tracking-widest font-label-sm" data-id="${insight.id}">
            <span class="material-symbols-outlined text-sm" data-icon="check">check</span>
            Verify
          </button>
          <button class="btn-reject-insight p-1.5 rounded-full border border-outline-variant/20 text-outline hover:text-error hover:border-error/30 transition-all" data-id="${insight.id}" title="Reject">
            <span class="material-symbols-outlined text-sm" data-icon="close">close</span>
          </button>
        </div>
      </div>`;
  }

  return `
    <div class="flex items-start gap-5 py-5 border-b border-outline-variant/10 last:border-0 group">
      <div class="flex flex-col items-center gap-1 shrink-0 w-12 text-center">
        <span class="text-[18px] font-display-lg text-primary tabular-nums">${dateStr.split(' ')[1]}</span>
        <span class="text-[9px] uppercase tracking-widest text-outline opacity-50 font-label-sm">${dateStr.split(' ')[0]}</span>
      </div>
      <div class="flex-1 min-w-0 space-y-1.5">
        <p class="text-sm font-body-md text-on-surface leading-relaxed group-hover:text-white transition-colors">${insight.content}</p>
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-xs" data-icon="check_circle">check_circle</span>
          <span class="text-[10px] uppercase tracking-widest text-outline font-label-sm opacity-50">${source}</span>
          <span class="text-[10px] text-outline opacity-30">·</span>
          <span class="text-[10px] uppercase tracking-widest text-outline font-label-sm opacity-50">${ago}</span>
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
    <header class="px-12 pt-12 pb-8 shrink-0">
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
      <section id="hero-section">
        <div class="flex items-center justify-between mb-8">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-2xl bg-primary/15 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary text-2xl" data-icon="auto_awesome">auto_awesome</span>
            </div>
            <div>
              <h2 class="text-2xl font-headline-sm text-on-surface uppercase tracking-[0.15em]">Intelligence Brief</h2>
              <p class="text-[10px] uppercase tracking-[0.25em] text-primary-fixed-dim opacity-50 font-label-sm mt-0.5">AI synthesis of verified insights</p>
            </div>
          </div>
          <!-- Day selector -->
          <div class="flex items-center gap-1 p-1 bg-surface-container-low rounded-full border border-outline-variant/10" id="day-selector">
            ${DAY_OPTIONS.map(d => `
              <button class="day-btn px-3 py-1.5 rounded-full text-[10px] font-label-sm uppercase tracking-widest transition-all duration-200 ${d === activeDays ? 'bg-primary text-on-primary' : 'text-outline hover:text-on-surface'}" data-days="${d}">${d}d</button>
            `).join('')}
          </div>
        </div>
        <div id="hero-content" class="glass-panel p-12 rounded-[2rem] border-primary/15 bg-primary/[0.03] relative overflow-hidden shadow-2xl shadow-primary/5">
          <div class="absolute -top-24 -right-24 w-72 h-72 bg-primary/10 rounded-full blur-[100px] pointer-events-none"></div>
          <div class="absolute -bottom-16 -left-16 w-48 h-48 bg-tertiary/5 rounded-full blur-[80px] pointer-events-none"></div>
          <div id="hero-text" class="relative z-10">
            <div class="flex items-center gap-3 opacity-40">
              <span class="material-symbols-outlined animate-spin" data-icon="progress_activity">progress_activity</span>
              <span class="text-sm uppercase tracking-widest font-label-sm">Synthesizing intelligence…</span>
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
        ${banCard(stats.verified_count, 'Verified Insights', 'verified', 'text-primary')}
        ${banCard(stats.analyses_count, 'Total Analyses', 'analytics', 'text-secondary')}
        ${banCard(stats.contributors_count, 'Insight Contributors', 'group', 'text-tertiary')}
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
      .map(l => l.replace(/^[-*•]\s*/, '').trim())
      .filter(l => l.length > 10);

    const isExpandable = allBullets.length > 4;
    const bullets = isExpandable ? allBullets.slice(0, 4) : allBullets;
    const hiddenBullets = isExpandable ? allBullets.slice(4) : [];

    const renderBullet = (b: string) => `
      <li class="flex items-start gap-4 group/item">
        <span class="material-symbols-outlined text-primary text-base mt-0.5 shrink-0 opacity-70 group-hover/item:opacity-100 transition-opacity" data-icon="arrow_right">arrow_right</span>
        <span class="text-base font-body-lg text-on-surface-variant leading-relaxed group-hover/item:text-on-surface transition-colors">${b}</span>
      </li>`;

    const bulletHtml = bullets.length > 0
      ? bullets.map(renderBullet).join('')
      : `<li class="text-on-surface-variant opacity-60 font-body-md text-sm">${data.summary}</li>`;

    const countNote = data.insight_count > 0
      ? `<div class="pt-6 border-t border-outline-variant/10 flex items-center gap-2 opacity-40 mt-8">
          <span class="material-symbols-outlined text-sm" data-icon="analytics">analytics</span>
          <span class="text-[10px] uppercase tracking-widest text-outline font-label-sm">${data.insight_count} verified insight${data.insight_count !== 1 ? 's' : ''} · last ${data.days}d</span>
        </div>`
      : '';

    heroText.innerHTML = `
      <ul id="hero-bullets" class="space-y-5 list-none">${bulletHtml}</ul>
      ${isExpandable ? `
        <div id="hidden-bullets" class="hidden space-y-5 mt-5 animate-in fade-in slide-in-from-top-2 duration-300">
          ${hiddenBullets.map(renderBullet).join('')}
        </div>
        <button id="btn-toggle-hero" class="mt-8 flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-primary hover:text-primary-fixed transition-all font-label-sm group">
          <span class="material-symbols-outlined text-sm group-hover:translate-y-0.5 transition-transform" data-icon="expand_more">expand_more</span>
          <span>Expand Brief</span>
        </button>
      ` : ''}
      ${countNote}`;

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
        ? `<div class="flex flex-col items-center gap-3 py-12 text-center opacity-40">
            <span class="material-symbols-outlined text-3xl" data-icon="inbox">inbox</span>
            <p class="text-xs uppercase tracking-widest font-label-sm">Queue is clear</p>
          </div>`
        : items.map(i => insightPill(i, 'queue')).join('');

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
      ? `<div class="flex flex-col items-center gap-3 py-12 text-center opacity-40">
          <span class="material-symbols-outlined text-3xl" data-icon="newspaper">newspaper</span>
          <p class="text-xs uppercase tracking-widest font-label-sm">No verified insights yet</p>
        </div>`
      : feed.map(i => insightPill(i, 'feed')).join('');
  } catch {
    feedEl.innerHTML = `<p class="text-sm text-outline opacity-50">Failed to load feed.</p>`;
  }
}
