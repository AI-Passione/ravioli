import { store } from '../store';
import { api } from '../services/api';
import { format } from 'date-fns';

// --- Safety Helpers ---
function escapeHTML(str: string): string {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function sanitizeImageUrl(input: string): string | null {
  const value = input.trim();
  if (!value) return null;

  // Allow root-relative paths only (disallow protocol-relative //example.com)
  if (value.startsWith('/') && !value.startsWith('//')) {
    return value;
  }

  // Allow only http(s) absolute URLs
  try {
    const parsed = new URL(value);
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.toString();
    }
  } catch {
    // Invalid URL
  }

  return null;
}

// --- Notion compatibility helpers ---
function getBlocksPreview(blocks?: any[]): string {
  if (!blocks || blocks.length === 0) return 'No content codified.';
  const firstBlock = blocks.find(b => b.type === 'paragraph');
  if (!firstBlock) return 'Abstract block data...';
  const rt = firstBlock.paragraph?.rich_text?.[0];
  if (!rt) return 'Empty block...';
  return rt.plain_text || rt.text?.content || 'Empty block...';
}

function textToBlocks(text: string): any[] {
  return [{
    type: 'paragraph',
    paragraph: {
      rich_text: [{ type: 'text', text: { content: text }, plain_text: text }]
    }
  }];
}

function getIconDisplay(icon?: any): string {
  if (!icon) return '📄';
  if (icon.type === 'emoji') return icon.emoji;
  return '📄';
}

function getCoverUrl(cover?: any): string {
  if (!cover) return '';
  if (cover.type === 'external') return cover.external.url;
  if (cover.type === 'file') return cover.file.url;
  return '';
}
// ------------------------------------

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
          <span class="text-[10px] uppercase tracking-[0.3em] text-primary font-medium">Intelligence Core</span>
        </div>
        <h1 class="text-5xl font-headline-lg text-white tracking-tight">Knowledge Base</h1>
        <p class="text-on-surface-variant font-body-lg max-w-2xl">
          Codified domain intelligence structured as Page Properties and Page Content (Blocks) for maximum analytical alignment.
        </p>
      </div>
      <button id="add-knowledge-btn" class="px-8 py-4 rounded-2xl bg-primary text-on-primary font-headline-sm hover:brightness-110 hover:scale-[1.02] transition-all flex items-center gap-3 shadow-2xl shadow-primary/20 active:scale-[0.98]">
        <span class="material-symbols-outlined">add_circle</span>
        Codify New Page
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
      <p class="text-sm uppercase tracking-widest opacity-50">Establish your first Page</p>
    </div>
  ` : `
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative z-10 pb-20">
      ${pages.map((page, index) => {
    const coverUrl = getCoverUrl(page.cover);
    const coverStyle = coverUrl
      ? `background-image: url('${escapeHTML(coverUrl)}'); background-size: cover; background-position: center;`
      : `background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.1) 0%, rgba(var(--tertiary-rgb), 0.05) 100%);`;

    return `
          <div class="glass-panel rounded-[2.5rem] border-primary/5 hover:border-primary/20 transition-all duration-500 group cursor-pointer flex flex-col hover:shadow-2xl hover:shadow-primary/5 animate-reveal overflow-hidden" style="animation-delay: ${index * 0.05}s" data-id="${page.id}">
            <!-- Cover -->
            <div class="h-32 w-full relative" style="${coverStyle}">
              <div class="absolute inset-0 bg-gradient-to-t from-surface/80 to-transparent"></div>
              <div class="absolute top-4 right-4 flex gap-2">
                <span class="px-3 py-1 rounded-full bg-surface/40 backdrop-blur-md text-[9px] font-bold uppercase tracking-widest text-white border border-white/10">
                  ${escapeHTML(page.ownership_type)}
                </span>
                ${page.parent_id ? `
                   <span class="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary backdrop-blur-md" title="Nested Page">
                    <span class="material-symbols-outlined text-[14px]">account_tree</span>
                   </span>
                ` : ''}
              </div>
            </div>

            <!-- Content Area -->
            <div class="p-8 pt-0 -mt-6 relative z-10 flex-1 flex flex-col">
              <!-- Icon -->
              <div class="w-14 h-14 rounded-2xl bg-surface-container-high border border-outline-variant/20 text-3xl flex items-center justify-center mb-4 shadow-xl group-hover:scale-110 transition-transform duration-500">
                ${escapeHTML(getIconDisplay(page.icon))}
              </div>

              <h3 class="text-2xl font-headline-md text-white mb-3 group-hover:text-primary transition-colors duration-300">${escapeHTML(page.title)}</h3>
              <p class="text-on-surface-variant line-clamp-3 text-sm leading-relaxed mb-8 flex-1 group-hover:text-on-surface transition-colors">
                ${escapeHTML(getBlocksPreview(page.content))}
              </p>
              
              <div class="flex items-center justify-between mt-auto pt-6 border-t border-outline-variant/10 text-[10px] text-outline uppercase tracking-[0.2em] font-medium">
                <span class="flex items-center gap-2">
                  <span class="w-1 h-1 rounded-full bg-outline/30"></span>
                  ${format(new Date(page.updated_at), 'MMM d, yyyy')}
                </span>
                <div class="flex gap-4">
                  <button class="edit-page text-primary hover:text-white transition-colors flex items-center gap-1" data-id="${page.id}">
                    <span class="material-symbols-outlined text-sm">edit_note</span>
                    Details
                  </button>
                </div>
              </div>
            </div>
          </div>
        `;
  }).join('')}
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

  return container;
}

function renderKnowledgeEditor(id?: string) {
  const existing = id ? store.getKnowledgePages().find(p => p.id === id) : null;
  const allPages = store.getKnowledgePages().filter(p => p.id !== id);

  const modal = document.createElement('div');
  modal.className = 'fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-500';

  const coverUrl = getCoverUrl(existing?.cover);
  const iconDisplay = getIconDisplay(existing?.icon);

  modal.innerHTML = `
        <div class="glass-panel w-full max-w-4xl rounded-[3.5rem] border-primary/20 overflow-hidden relative animate-in zoom-in slide-in-from-bottom-12 duration-700 ease-out shadow-[0_0_100px_rgba(var(--primary-rgb),0.1)] flex flex-col max-h-[90vh]">
             <!-- Page Aesthetics Section -->
             <div class="h-48 w-full relative bg-surface-container-high overflow-hidden" id="editor-cover-preview">
                ${coverUrl ? `<img src="${escapeHTML(coverUrl)}" class="w-full h-full object-cover">` : '<div class="w-full h-full bg-gradient-to-br from-primary/10 to-tertiary/5"></div>'}
                <div class="absolute inset-0 bg-gradient-to-t from-surface via-transparent to-transparent"></div>
                <div class="absolute top-8 right-8 flex gap-3">
                    <button id="close-modal" class="w-12 h-12 rounded-2xl bg-surface/40 backdrop-blur-md flex items-center justify-center hover:bg-error/20 hover:text-error transition-all duration-300 group">
                        <span class="material-symbols-outlined text-white group-hover:text-error transition-colors">close</span>
                    </button>
                </div>
                <div class="absolute bottom-0 left-12 transform translate-y-1/2">
                   <div class="relative group">
                    <input type="text" id="icon-input" name="icon_emoji" value="${escapeHTML(iconDisplay)}" 
                        class="w-20 h-20 rounded-3xl bg-surface-container-highest border-2 border-primary/20 text-4xl flex items-center justify-center text-center outline-none focus:border-primary transition-all shadow-2xl cursor-pointer">
                    <div class="absolute inset-0 flex items-center justify-center bg-black/40 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                        <span class="material-symbols-outlined text-white text-sm">emoji_emotions</span>
                    </div>
                   </div>
                </div>
             </div>

             <div class="p-12 pt-16 overflow-y-auto custom-scrollbar flex-1">
                <form id="knowledge-form" class="space-y-10">
                    <!-- Section 1: Page Properties -->
                    <div class="space-y-8">
                        <div class="grid grid-cols-12 gap-8">
                            <div class="col-span-8 space-y-3">
                                <label class="text-[10px] uppercase tracking-[0.3em] text-primary font-bold ml-2">Page Title</label>
                                <input type="text" name="title" value="${escapeHTML(existing?.title || '')}" placeholder="Untitled" 
                                    class="w-full bg-transparent border-none text-5xl font-headline-lg text-white placeholder:text-outline/20 focus:ring-0 transition-all outline-none p-0" required>
                            </div>
                            <div class="col-span-4 space-y-3">
                                <label class="text-[10px] uppercase tracking-[0.3em] text-primary font-bold ml-2">Access Type</label>
                                <div class="flex gap-2 p-1.5 bg-surface-container-high border border-outline-variant/20 rounded-2xl w-full">
                                    <button type="button" data-value="individual" class="ownership-toggle flex-1 py-3 rounded-xl transition-all font-headline-sm ${(!existing || existing.ownership_type === 'individual') ? 'bg-primary text-on-primary shadow-lg shadow-primary/20' : 'text-outline/50 hover:text-white'}">Individual</button>
                                    <button type="button" data-value="team" class="ownership-toggle flex-1 py-3 rounded-xl transition-all font-headline-sm ${existing?.ownership_type === 'team' ? 'bg-primary text-on-primary shadow-lg shadow-primary/20' : 'text-outline/50 hover:text-white'}">Team</button>
                                    <input type="hidden" name="ownership_type" value="${escapeHTML(existing?.ownership_type || 'individual')}">
                                </div>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-8">
                            <div class="space-y-3">
                                <label class="text-[10px] uppercase tracking-[0.3em] text-outline font-bold ml-2">Cover URL</label>
                                <input type="text" id="cover-input" name="cover_url" value="${escapeHTML(coverUrl)}" placeholder="https://..." 
                                    class="w-full bg-surface-container-high border border-outline-variant/20 rounded-2xl px-6 py-4 text-white placeholder:text-outline/30 focus:border-primary/50 transition-all outline-none">
                            </div>
                            <div class="space-y-3">
                                <label class="text-[10px] uppercase tracking-[0.3em] text-outline font-bold ml-2">Parent Page</label>
                                <select name="parent_id" class="w-full bg-surface-container-high border border-outline-variant/20 rounded-2xl px-6 py-4 text-white appearance-none outline-none focus:border-primary/50 transition-all">
                                    <option value="">No Parent</option>
                                    ${allPages.map(p => `<option value="${p.id}" ${existing?.parent_id === p.id ? 'selected' : ''}>${escapeHTML(p.title)}</option>`).join('')}
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Section 2: Page Content (Blocks) -->
                    <div class="space-y-3 pt-6 border-t border-outline-variant/10">
                        <label class="text-[10px] uppercase tracking-[0.3em] text-primary font-bold ml-2">Page Content (Blocks Preview)</label>
                        <textarea name="raw_content" rows="12" placeholder="Start typing page content here... This will be codified into blocks." 
                            class="w-full bg-transparent border-none text-xl leading-relaxed text-on-surface-variant placeholder:text-outline/20 focus:ring-0 transition-all outline-none resize-none min-h-[300px]" required>${escapeHTML(getBlocksPreview(existing?.content))}</textarea>
                    </div>

                    <div class="flex gap-4 pt-8 sticky bottom-0 bg-surface/80 backdrop-blur-md pb-4">
                        <button type="submit" class="flex-1 bg-primary text-on-primary py-5 rounded-3xl font-headline-md hover:brightness-110 hover:scale-[1.01] transition-all shadow-2xl shadow-primary/20 active:scale-[0.99] flex items-center justify-center gap-3">
                            <span class="material-symbols-outlined">${id ? 'auto_fix' : 'add_task'}</span>
                            ${id ? 'Update Intelligence' : 'Establish Page'}
                        </button>
                        ${id ? `
                            <button type="button" id="delete-btn" class="px-8 bg-error/10 text-error rounded-3xl hover:bg-error hover:text-white transition-all duration-300">
                                <span class="material-symbols-outlined">delete</span>
                            </button>
                        ` : ''}
                    </div>
                </form>
             </div>
        </div>
    `;

  document.body.appendChild(modal);

  const form = modal.querySelector('#knowledge-form') as HTMLFormElement;
  const closeBtn = modal.querySelector('#close-modal');
  const deleteBtn = modal.querySelector('#delete-btn');
  const toggles = modal.querySelectorAll('.ownership-toggle');
  const hiddenOwnershipInput = modal.querySelector('input[name="ownership_type"]') as HTMLInputElement;
  const coverInput = modal.querySelector('#cover-input') as HTMLInputElement;
  const coverPreview = modal.querySelector('#editor-cover-preview');

  // Live Cover Update
  coverInput.addEventListener('input', () => {
    const val = coverInput.value;
    const safeUrl = sanitizeImageUrl(val);
    const img = coverPreview!.querySelector('img');
    if (safeUrl) {
      if (img) img.src = safeUrl;
      else {
        const newImg = document.createElement('img');
        newImg.src = safeUrl;
        newImg.className = 'w-full h-full object-cover';
        coverPreview!.prepend(newImg);
        coverPreview!.querySelector('.bg-gradient-to-br')?.remove();
      }
    }
  });

  toggles.forEach(t => {
    t.addEventListener('click', () => {
      const val = t.getAttribute('data-value')!;
      hiddenOwnershipInput.value = val;
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

  deleteBtn?.addEventListener('click', async () => {
    if (id && confirm('Delete this intelligence page?')) {
      await api.deleteKnowledgePage(id);
      const pages = await api.listKnowledgePages();
      store.setKnowledgePages(pages);
      closeModal();
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]') as HTMLButtonElement;
    submitBtn.disabled = true;

    const formData = new FormData(form);
    const title = formData.get('title') as string;
    const rawContent = formData.get('raw_content') as string;
    const coverUrl = formData.get('cover_url') as string;
    const iconEmoji = formData.get('icon_emoji') as string;
    const ownership = formData.get('ownership_type') as 'individual' | 'team';
    const parentId = (formData.get('parent_id') as string) || undefined;

    const data: any = {
      title,
      ownership_type: ownership,
      parent_id: parentId,
      properties: {
        title: [{ type: 'text', text: { content: title } }],
        ownership: { select: { name: ownership } }
      },
      content: textToBlocks(rawContent),
      icon: { type: 'emoji', emoji: iconEmoji || '📄' },
      cover: coverUrl ? { type: 'external', external: { url: coverUrl } } : null
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
      console.error('Failed to save', err);
      submitBtn.disabled = false;
      alert('Sync failed.');
    }
  });
}
