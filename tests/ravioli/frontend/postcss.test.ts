import { describe, it, expect } from 'vitest';
import postcss from 'postcss';
import tailwindcss from '@tailwindcss/postcss';

describe('PostCSS Configuration', () => {
  it('should process Tailwind directives using @tailwindcss/postcss', async () => {
    // Tailwind v4 uses @import "tailwindcss" but supports legacy @tailwind directives
    const input = '@tailwind utilities; .custom-class { @apply flex justify-center; }';
    
    try {
      const result = await postcss([tailwindcss()]).process(input, { from: 'src/test.css' });
      
      // Verify that the @apply directive was processed
      expect(result.css).toContain('display: flex');
      expect(result.css).toContain('justify-content: center');
      
      // Verify no errors were thrown
      expect(result.warnings()).toHaveLength(0);
    } catch (error) {
      console.error('PostCSS processing failed:', error);
      throw error;
    }
  });

  it('should be able to load the actual postcss.config.js', async () => {
    // This is a more direct test of the configuration file itself
    const configPath = '../../../src/ravioli/frontend/postcss.config.js';
    const config = await import(configPath);
    
    expect(config.default).toBeDefined();
    expect(config.default.plugins).toBeDefined();
    expect(config.default.plugins['@tailwindcss/postcss']).toBeDefined();
    expect(config.default.plugins['autoprefixer']).toBeDefined();
  });
});
