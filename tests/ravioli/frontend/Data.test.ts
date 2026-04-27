import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderData } from '../../../src/ravioli/frontend/src/components/Data';
import { store } from '../../../src/ravioli/frontend/src/store';

describe('Data component', () => {
  beforeEach(() => {
    // Clear store state
    store.setDataSources([]);
    
    // Mock refreshFiles behavior (which calls reload)
    // We don't want tests to actually reload
    vi.stubGlobal('location', { reload: vi.fn() });
    
    // Mock window.alert
    vi.stubGlobal('alert', vi.fn());
  });

  it('should render the "Data Sources" heading', () => {
    const el = renderData();
    expect(el.innerHTML).toContain('Data Sources');
  });

  it('should show an empty state when no files are present', () => {
    const el = renderData();
    expect(el.innerHTML).toContain('No assets ingested yet');
  });

  it('should render a list of uploaded files', () => {
    store.setDataSources([
      {
        id: '1',
        filename: 'test.csv',
        original_filename: 'My Data',
        content_type: 'text/csv',
        size_bytes: 1024,
        table_name: 'my_data',
        schema_name: 'main',
        row_count: 100,
        status: 'completed',
        source_type: 'file',
        has_pii: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ]);
    
    const el = renderData();
    expect(el.innerHTML).toContain('My Data');
    expect(el.innerHTML).toContain('my_data');
    expect(el.innerHTML).toContain('100');
    // Should have a file icon
    expect(el.innerHTML).toContain('description');
  });

  it('should render WFS API sources with correct icon', () => {
    store.setDataSources([
      {
        id: '2',
        filename: 'wfs_data',
        original_filename: 'Berlin Traffic',
        content_type: 'application/wfs',
        size_bytes: 0,
        table_name: 'traffic',
        schema_name: 's_geoserver',
        row_count: 50,
        status: 'completed',
        source_type: 'wfs',
        source_url: 'https://api.example.com',
        has_pii: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ]);
    
    const el = renderData();
    expect(el.innerHTML).toContain('Berlin Traffic');
    // Should have an API icon
    expect(el.innerHTML).toContain('api');
  });

  it('should open the "Add Source" modal when clicking the button', () => {
    const el = renderData();
    const btn = el.querySelector('#btn-add-source') as HTMLButtonElement;
    const modal = el.querySelector('#add-source-modal') as HTMLElement;
    
    expect(modal.classList.contains('hidden')).toBe(true);
    
    btn.click();
    
    expect(modal.classList.contains('hidden')).toBe(false);
    expect(el.innerHTML).toContain('Select ingestion method');
  });

  it('should navigate to WFS step in modal', () => {
    const el = renderData();
    (el.querySelector('#btn-add-source') as HTMLButtonElement).click();
    
    const wfsCard = el.querySelector('.source-type-card[data-type="wfs"]') as HTMLElement;
    wfsCard.click();
    
    const stepWfs = el.querySelector('#step-wfs') as HTMLElement;
    expect(stepWfs.classList.contains('hidden')).toBe(false);
  });

  it('should navigate back to selection from WFS step', () => {
    const el = renderData();
    (el.querySelector('#btn-add-source') as HTMLButtonElement).click();
    
    (el.querySelector('.source-type-card[data-type="wfs"]') as HTMLElement).click();
    (el.querySelector('#step-wfs .btn-back') as HTMLElement).click();
    
    expect(el.querySelector('#step-selection')?.classList.contains('hidden')).toBe(false);
  });

  it('should render a PII tag and handle dismissal', () => {
    store.setDataSources([
      {
        id: 'pii-1',
        filename: 'pii.csv',
        original_filename: 'PII Data',
        content_type: 'text/csv',
        size_bytes: 100,
        table_name: 'pii_data',
        schema_name: 'main',
        row_count: 5,
        status: 'completed',
        source_type: 'file',
        has_pii: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    ]);
    
    const el = renderData();
    const piiBadge = el.querySelector('.pii-badge');
    expect(piiBadge).not.toBeNull();
    expect(piiBadge?.textContent).toContain('PII');
    
    // Test dismissal button presence
    const dismissBtn = el.querySelector('.btn-dismiss-pii');
    expect(dismissBtn).not.toBeNull();
  });
});
