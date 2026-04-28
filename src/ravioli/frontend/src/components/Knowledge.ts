import { store } from '../store';
import { api } from '../services/api';
import { format } from 'date-fns';

export function renderKnowledge() {
  const container = document.createElement('main');
  container.className = 'flex-1 ml-64 h-full overflow-y-auto bg-surface relative p-12 custom-scrollbar';
  
  const pages = store.getKnowledgePages();
  
  // Header
  const header = `
    <div class="flex items-end justify-between mb-12 relative z-10">
      <div class="space-y-2">
        <div class="flex items-center gap-3 mb-2">
          <div class="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
          <span class="text-[10px] uppercase tracking-[0.3em] text-primary font-medium">Domain Intelligence</span>
        </div>
        <h1 class="text-5xl font-headline-lg text-white tracking-tight">Knowledge Base</h1>
        <p class="text-on-surface-variant font-body-lg max-w-2xl">
          The sanctuary for codified domain expertise. Establish your analytical foundation by documentating unique business contexts and strategic frameworks.
        </p>
      </div>
      <button id="add-knowledge-btn" class="px-8 py-4 rounded-2xl bg-primary text-on-primary font-headline-sm hover:brightness-110 hover:scale-[1.02] transition-all flex items-center gap-3 shadow-2xl shadow-primary/20 active:scale-[0.98]">
        <span class="material-symbols-outlined">add_circle</span>
        Codify Intelligence
      </button>
    </div>
  `;

  // List
  const listContent = pages.length === 0 ? `
    <div class="h-[60vh] flex flex-col items-center justify-center border-2 border-dashed border-outline-variant/20 rounded-[4rem] text-outline/50 relative z-10 group hover:border-primary/20 transition-colors duration-500">
      <div class="w-24 h-24 rounded-[2rem] bg-surface-container-high flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-500">
        <span class="material-symbols-outlined text-5xl">auto_stories</span>
      </div>
      <h3 class="text-xl text-white/50 font-headline-sm mb-2">No intelligence codified yet</h3>
      <p class="text-sm uppercase tracking-widest opacity-50">Click the button above to begin</p>
    </div>
  ` : `
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative z-10 pb-20">
      ${pages.map((page, index) => `
        <div class="glass-panel p-8 rounded-[2.5rem] border-primary/5 hover:border-primary/20 transition-all duration-500 group cursor-pointer flex flex-col hover:shadow-2xl hover:shadow-primary/5 animate-reveal" style="animation-delay: ${index * 0.05}s" data-id="${page.id}">
          <div class="flex items-start justify-between mb-6">
            <div class="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center group-hover:bg-primary group-hover:text-on-primary transition-all duration-500">
              <span class="material-symbols-outlined">${page.source === 'manual' ? 'edit_note' : 'link'}</span>
            </div>
            <div class="flex items-center gap-2">
               <span class="px-3 py-1 rounded-full bg-surface-container-high text-[9px] font-bold uppercase tracking-widest text-on-surface-variant border border-outline-variant/30 group-hover:border-primary/30 transition-colors">
                ${page.ownership_type}
              </span>
            </div>
          </div>
          <h3 class="text-2xl font-headline-md text-white mb-3 group-hover:text-primary transition-colors duration-300">${page.title}</h3>
          <p class="text-on-surface-variant line-clamp-4 text-sm leading-relaxed mb-8 flex-1 group-hover:text-on-surface transition-colors">${page.content}</p>
          <div class="flex items-center justify-between mt-auto pt-6 border-t border-outline-variant/10 text-[10px] text-outline uppercase tracking-[0.2em] font-medium">
            <span class="flex items-center gap-2">
              <span class="w-1 h-1 rounded-full bg-outline/30"></span>
              ${format(new Date(page.updated_at), 'MMM d, yyyy')}
            </span>
            <div class="flex gap-4">
              <button class="edit-page text-primary hover:text-white transition-colors flex items-center gap-1" data-id="${page.id}">
                <span class="material-symbols-outlined text-sm">edit</span>
                Edit
              </button>
              <button class="delete-page text-error/60 hover:text-error transition-colors flex items-center gap-1" data-id="${page.id}">
                <span class="material-symbols-outlined text-sm">delete</span>
                Remove
              </button>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;

  container.innerHTML = `
    <div class="cinematic-vignette fixed inset-0 z-0 pointer-events-none opacity-50"></div>
    <div class="relative z-10 max-w-7xl mx-auto">
      ${header}
      ${listContent}
    </div>
  `;

  // Event Listeners
  container.querySelector('#add-knowledge-btn')?.addEventListener('click', () => {
    renderKnowledgeEditor();
  });

  container.querySelectorAll('.glass-panel').forEach(card => {
    card.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).closest('button')) return;
        const id = card.getAttribute('data-id');
        if (id) renderKnowledgeEditor(id);
    });
  });

  container.querySelectorAll('.edit-page').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        if (id) renderKnowledgeEditor(id);
    });
  });

  container.querySelectorAll('.delete-page').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        if (id && confirm('Are you sure you want to remove this intelligence from the knowledge base?')) {
            try {
                await api.deleteKnowledgePage(id);
                const pages = await api.listKnowledgePages();
                store.setKnowledgePages(pages);
            } catch (err) {
                console.error('Failed to delete knowledge', err);
            }
        }
    });
  });

  return container;
}

function renderKnowledgeEditor(id?: string) {
    const existing = id ? store.getKnowledgePages().find(p => p.id === id) : null;
    
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-500';
    
    modal.innerHTML = `
        <div class="glass-panel w-full max-w-3xl rounded-[3.5rem] border-primary/20 p-12 overflow-hidden relative animate-in zoom-in slide-in-from-bottom-12 duration-700 ease-out shadow-[0_0_100px_rgba(var(--primary-rgb),0.1)]">
             <div class="flex items-center justify-between mb-10">
                <div class="space-y-1">
                  <h2 class="text-4xl font-headline-lg text-white">${id ? 'Edit Intelligence' : 'Codify Intelligence'}</h2>
                  <p class="text-on-surface-variant text-sm">Refine the domain context for your analyses.</p>
                </div>
                <button id="close-modal" class="w-12 h-12 rounded-2xl bg-surface-container-high flex items-center justify-center hover:bg-error/20 hover:text-error transition-all duration-300 group">
                    <span class="material-symbols-outlined text-white group-hover:text-error transition-colors">close</span>
                </button>
            </div>

            <form id="knowledge-form" class="space-y-8">
                <div class="grid grid-cols-2 gap-6">
                  <div class="space-y-3">
                      <label class="text-[10px] uppercase tracking-[0.3em] text-primary font-bold ml-2">Intelligence Title</label>
                      <input type="text" name="title" value="${existing?.title || ''}" placeholder="e.g., Strategic Objectives 2024" 
                          class="w-full bg-surface-container-high border border-outline-variant/20 rounded-2xl px-6 py-4 text-white placeholder:text-outline/30 focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all outline-none" required>
                  </div>

                  <div class="space-y-3">
                      <label class="text-[10px] uppercase tracking-[0.3em] text-primary font-bold ml-2">Context Ownership</label>
                      <div class="flex gap-2 p-1.5 bg-surface-container-high border border-outline-variant/20 rounded-2xl w-full">
                          <button type="button" data-value="individual" class="ownership-toggle flex-1 py-3 rounded-xl transition-all font-headline-sm ${(!existing || existing.ownership_type === 'individual') ? 'bg-primary text-on-primary shadow-lg shadow-primary/20' : 'text-outline/50 hover:text-white'}">Individual</button>
                          <button type="button" data-value="team" class="ownership-toggle flex-1 py-3 rounded-xl transition-all font-headline-sm ${existing?.ownership_type === 'team' ? 'bg-primary text-on-primary shadow-lg shadow-primary/20' : 'text-outline/50 hover:text-white'}">Team</button>
                          <input type="hidden" name="ownership_type" value="${existing?.ownership_type || 'individual'}">
                      </div>
                  </div>
                </div>

                <div class="space-y-3">
                    <label class="text-[10px] uppercase tracking-[0.3em] text-primary font-bold ml-2">Intelligence Content (Markdown supported)</label>
                    <textarea name="content" rows="12" placeholder="Codify the domain context here. This information will be used to ground AI agents during analysis..." 
                        class="w-full bg-surface-container-high border border-outline-variant/20 rounded-[2.5rem] px-8 py-8 text-white placeholder:text-outline/30 focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all outline-none resize-none custom-scrollbar" required>${existing?.content || ''}</textarea>
                </div>

                <div class="flex gap-4 pt-4">
                    <button type="submit" class="flex-1 bg-primary text-on-primary py-5 rounded-2xl font-headline-md hover:brightness-110 hover:scale-[1.01] transition-all shadow-2xl shadow-primary/20 active:scale-[0.99] flex items-center justify-center gap-3">
                        <span class="material-symbols-outlined">${id ? 'save' : 'auto_fix'}</span>
                        ${id ? 'Save Changes' : 'Codify Intelligence'}
                    </button>
                </div>
            </form>
        </div>
    `;

    document.body.appendChild(modal);

    const form = modal.querySelector('#knowledge-form') as HTMLFormElement;
    const closeBtn = modal.querySelector('#close-modal');
    const toggles = modal.querySelectorAll('.ownership-toggle');
    const hiddenInput = modal.querySelector('input[name="ownership_type"]') as HTMLInputElement;

    toggles.forEach(t => {
        t.addEventListener('click', () => {
            const val = t.getAttribute('data-value')!;
            hiddenInput.value = val;
            toggles.forEach(btn => {
                if (btn === t) {
                    btn.classList.add('bg-primary', 'text-on-primary', 'shadow-lg', 'shadow-primary/20');
                    btn.classList.remove('text-outline/50');
                } else {
                    btn.classList.remove('bg-primary', 'text-on-primary', 'shadow-lg', 'shadow-primary/20');
                    btn.classList.add('text-outline/50');
                }
            });
        });
    });

    const closeModal = () => {
        modal.classList.add('animate-out', 'fade-out');
        modal.firstElementChild?.classList.add('animate-out', 'zoom-out', 'slide-out-to-bottom-12');
        setTimeout(() => modal.remove(), 500);
    };

    closeBtn?.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]') as HTMLButtonElement;
        const originalContent = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<div class="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> Codifying...`;

        const formData = new FormData(form);
        const data = {
            title: formData.get('title') as string,
            content: formData.get('content') as string,
            ownership_type: formData.get('ownership_type') as 'individual' | 'team',
        };

        try {
            if (id) {
                await api.updateKnowledgePage(id, data);
            } else {
                await api.createKnowledgePage(data);
            }
            const pages = await api.listKnowledgePages();
            store.setKnowledgePages(pages);
            closeModal();
        } catch (err) {
            console.error('Failed to save knowledge', err);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalContent;
            alert('Failed to save knowledge. Please verify your connection to the intelligence core.');
        }
    });
}
