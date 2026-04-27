import { api } from '../services/api';
import { formatDistanceToNow } from 'date-fns';
import type { Insight } from '../types';
import { clearInsightsCache } from './Insights';

export function renderGovernance() {
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 overflow-y-auto bg-background h-screen flex flex-col custom-scrollbar';

  container.innerHTML = `
    <!-- Page Header -->
    <header class="px-12 pt-12 pb-8 shrink-0 animate-reveal">
      <div class="space-y-2">
        <p class="text-[10px] uppercase tracking-[0.3em] text-primary-fixed-dim opacity-60 font-label-sm">Administrative Control</p>
        <h1 class="font-display-lg text-4xl text-on-surface tracking-tight">Governance</h1>
        <p class="text-sm text-on-surface-variant font-body-md opacity-60">Manage platform integrity, access controls, and data verification.</p>
      </div>
      <div class="mt-8 h-px bg-gradient-to-r from-primary/20 via-outline-variant/20 to-transparent"></div>
    </header>

    <div class="flex-1 px-12 pb-16 space-y-12">
      
      <!-- Horizontal Tabs for Governance Sub-sections -->
      <div class="flex items-center gap-8 border-b border-white/5 pb-1">
        <button class="gov-tab-btn active pb-4 text-[10px] uppercase tracking-[0.2em] font-bold text-primary border-b-2 border-primary transition-all" data-tab="review">Review Queue</button>
        <button class="gov-tab-btn pb-4 text-[10px] uppercase tracking-[0.2em] font-bold text-outline hover:text-white transition-all opacity-50 cursor-not-allowed" data-tab="users">Users</button>
        <button class="gov-tab-btn pb-4 text-[10px] uppercase tracking-[0.2em] font-bold text-outline hover:text-white transition-all opacity-50 cursor-not-allowed" data-tab="permissions">Permissions</button>
        <button class="gov-tab-btn pb-4 text-[10px] uppercase tracking-[0.2em] font-bold text-outline hover:text-white transition-all opacity-50 cursor-not-allowed" data-tab="groups">Groups</button>
      </div>

      <!-- Tab Content Area -->
      <div id="gov-content" class="animate-reveal stagger-1">
        
        <!-- Review Queue Section -->
        <section id="review-section" class="space-y-8">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-tertiary/10 flex items-center justify-center border border-tertiary/20">
                <span class="material-symbols-outlined text-tertiary" data-icon="pending_actions">pending_actions</span>
              </div>
              <div>
                <h2 class="text-xl font-headline-sm text-on-surface uppercase tracking-[0.15em]">Pending Verification</h2>
                <p class="text-[10px] uppercase tracking-[0.2em] text-outline opacity-40 font-medium">Verify AI-generated insights before they reach the main feed</p>
              </div>
            </div>
            <span id="queue-badge" class="px-3 py-1 rounded-full bg-tertiary/10 text-tertiary text-[10px] font-bold uppercase tracking-widest hidden">0</span>
          </div>

          <div id="review-queue" class="grid grid-cols-1 gap-4 max-w-4xl">
            <div class="h-32 rounded-3xl bg-surface-container-low animate-pulse"></div>
            <div class="h-32 rounded-3xl bg-surface-container-low animate-pulse"></div>
          </div>
        </section>

      </div>
    </div>
  `;

  hydrateQueue(container);

  return container;
}

function insightReviewCard(insight: Insight) {
  const ago = formatDistanceToNow(new Date(insight.created_at), { addSuffix: true });
  const source = insight.source_label ?? 'Unknown analysis';

  return `
    <div class="review-item flex items-start gap-6 p-6 rounded-3xl glass-card border-white/5 hover:border-tertiary/30 transition-all duration-500 group insight-card-hover" data-insight-id="${insight.id}">
      <div class="w-2.5 h-2.5 rounded-full bg-tertiary mt-2.5 shrink-0 animate-pulse shadow-[0_0_12px_rgba(var(--tertiary-rgb),0.5)]"></div>
      <div class="flex-1 min-w-0 space-y-3">
        <p class="text-base font-body-md text-on-surface leading-relaxed group-hover:text-white transition-colors duration-300">${insight.content}</p>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1.5 opacity-40">
            <span class="material-symbols-outlined text-sm" data-icon="analytics">analytics</span>
            <span class="text-[10px] uppercase tracking-[0.2em] font-bold">${source}</span>
          </div>
          <span class="text-[10px] text-outline opacity-20">|</span>
          <div class="flex items-center gap-1.5 opacity-40">
            <span class="material-symbols-outlined text-sm" data-icon="schedule">schedule</span>
            <span class="text-[10px] uppercase tracking-[0.2em] font-bold">${ago}</span>
          </div>
        </div>
      </div>
      <div class="flex flex-col gap-2 shrink-0 opacity-0 group-hover:opacity-100 transition-all duration-500 translate-x-4 group-hover:translate-x-0">
        <button class="btn-verify-insight flex items-center justify-center gap-2 px-6 py-3 rounded-2xl bg-primary text-on-primary shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all text-[11px] uppercase tracking-[0.2em] font-bold" data-id="${insight.id}">
          <span class="material-symbols-outlined text-sm" data-icon="check">check</span>
          Verify
        </button>
        <button class="btn-reject-insight flex items-center justify-center gap-2 px-6 py-3 rounded-2xl bg-surface-container-high text-outline hover:text-error hover:bg-error/10 border border-white/5 transition-all text-[11px] uppercase tracking-[0.2em] font-bold" data-id="${insight.id}">
          <span class="material-symbols-outlined text-sm" data-icon="close">close</span>
          Reject
        </button>
      </div>
    </div>`;
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
          badge.textContent = `${items.length} Pending`;
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      }
      queueEl.innerHTML = items.length === 0
        ? `<div class="glass-card flex flex-col items-center gap-5 py-24 text-center rounded-[3rem] border-dashed border-white/10 group animate-reveal">
            <div class="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 group-hover:bg-primary/10 transition-all duration-700">
              <span class="material-symbols-outlined text-5xl text-outline opacity-20 group-hover:text-primary group-hover:opacity-100 transition-all" data-icon="verified_user">verified_user</span>
            </div>
            <div class="space-y-2">
              <p class="text-sm uppercase tracking-[0.4em] font-bold text-on-surface opacity-60">Integrity Check Complete</p>
              <p class="text-xs uppercase tracking-[0.1em] text-outline opacity-30 font-medium">There are no insights awaiting verification at this time.</p>
            </div>
          </div>`
        : items.map((i, index) => `<div class="opacity-0 animate-reveal" style="animation-delay: ${index * 0.08}s">${insightReviewCard(i)}</div>`).join('');

      // Bind verify / reject buttons
      queueEl.querySelectorAll('.btn-verify-insight').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = btn.getAttribute('data-id');
          if (!id) return;
          btn.setAttribute('disabled', 'true');
          try {
            await api.verifyInsight(id);
            queue = queue.filter(i => i.id !== id);
            clearInsightsCache(); 
            render(queue);
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
          } catch {}
        });
      });
    };

    render(queue);
  } catch {
    queueEl.innerHTML = `<p class="text-sm text-outline opacity-50 p-12 text-center glass-card rounded-3xl">Failed to synchronize with governance server.</p>`;
  }
}
