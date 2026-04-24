import { describe, it, expect, beforeEach, vi } from 'vitest';
import { store } from '../../../src/ravioli/frontend/src/store';

describe('Settings navigation', () => {
  beforeEach(() => {
    store.setCurrentView('dashboard');
    store.setActiveAnalysisId(undefined);
  });

  it('should navigate to settings view', () => {
    store.setCurrentView('settings');
    expect(store.getCurrentView()).toBe('settings');
  });

  it('should clear active analysis when switching to settings', () => {
    store.setActiveAnalysisId('abc');
    store.setCurrentView('settings');
    expect(store.getActiveAnalysisId()).toBeUndefined();
  });

  it('should be able to navigate back to dashboard from settings', () => {
    store.setCurrentView('settings');
    store.setCurrentView('dashboard');
    expect(store.getCurrentView()).toBe('dashboard');
  });
});

describe('Settings component', () => {
  beforeEach(() => {
    // Mock fetch globally
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ key: 'ollama', value: {} }),
    }));
  });

  it('should render the Settings heading', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    expect(el.innerHTML).toContain('Settings');
  });

  it('should render AI Models section with Ollama', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    expect(el.innerHTML).toContain('AI Models');
    expect(el.innerHTML).toContain('Ollama');
  });

  it('should render a Configure button for Ollama by default', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    const btn = el.querySelector('#btn-configure-ollama');
    expect(btn).not.toBeNull();
  });

  it('should show mode options after clicking Configure', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    const btn = el.querySelector('#btn-configure-ollama') as HTMLButtonElement;
    btn.click();
    expect(el.innerHTML).toContain('Default');
    expect(el.innerHTML).toContain('Custom Local Runtime');
    expect(el.innerHTML).toContain('Ollama Cloud');
  });

  it('should hide Configure button once configuration panel is open', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    (el.querySelector('#btn-configure-ollama') as HTMLButtonElement).click();
    expect(el.querySelector('#btn-configure-ollama')).toBeNull();
  });

  it('should show cancel button and close panel on click', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    (el.querySelector('#btn-configure-ollama') as HTMLButtonElement).click();
    const cancelBtn = el.querySelector('#btn-cancel-ollama') as HTMLButtonElement;
    expect(cancelBtn).not.toBeNull();
    cancelBtn.click();
    expect(el.querySelector('#btn-configure-ollama')).not.toBeNull();
  });

  it('should render Gemini as coming soon', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    expect(el.innerHTML).toContain('Google Gemini');
    expect(el.innerHTML).toContain('Coming Soon');
  });

  it('should render Data Warehouses section with all placeholders', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    expect(el.innerHTML).toContain('Data Warehouses');
    expect(el.innerHTML).toContain('Motherduck');
    expect(el.innerHTML).toContain('BigQuery');
    expect(el.innerHTML).toContain('Snowflake');
  });

  it('should not show Base URL field when cloud mode is selected', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    (el.querySelector('#btn-configure-ollama') as HTMLButtonElement).click();
    // Switch to cloud by dispatching a change event (jsdom requires this for radio)
    const cloudRadio = el.querySelector('input[value="cloud"]') as HTMLInputElement;
    cloudRadio.checked = true;
    cloudRadio.dispatchEvent(new Event('change', { bubbles: true }));
    expect(el.querySelector('#ollama-base-url')).toBeNull();
    expect(el.querySelector('#ollama-api-key')).not.toBeNull();
  });

  it('should show Base URL field only for local mode', async () => {
    const { renderSettings } = await import('../../../src/ravioli/frontend/src/components/Settings');
    const el = renderSettings();
    (el.querySelector('#btn-configure-ollama') as HTMLButtonElement).click();
    const localRadio = el.querySelector('input[value="local"]') as HTMLInputElement;
    localRadio.checked = true;
    localRadio.dispatchEvent(new Event('change', { bubbles: true }));
    expect(el.querySelector('#ollama-base-url')).not.toBeNull();
    expect(el.querySelector('#ollama-api-key')).toBeNull();
  });
});
