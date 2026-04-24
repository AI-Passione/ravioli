import { describe, it, expect } from 'vitest';
import { formatBytes } from '../../../src/ravioli/frontend/src/utils/formatters';

describe('formatBytes', () => {
  it('formats zero bytes correctly', () => {
    expect(formatBytes(0)).toBe('0 Bytes');
  });

  it('formats bytes correctly', () => {
    expect(formatBytes(500)).toBe('500 Bytes');
  });

  it('formats KB correctly', () => {
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1536)).toBe('1.5 KB');
  });

  it('formats MB correctly', () => {
    expect(formatBytes(1048576)).toBe('1 MB');
    expect(formatBytes(2569011)).toBe('2.4 MB'); // 2569011 / (1024 * 1024) = 2.4499... -> 2.4
  });

  it('formats GB correctly', () => {
    expect(formatBytes(1073741824)).toBe('1 GB');
    expect(formatBytes(5905580032)).toBe('5.5 GB'); // 5.5 * 1024^3
  });

  it('respects decimals parameter', () => {
    expect(formatBytes(1536, 0)).toBe('2 KB'); // Math.round because of toFixed(0)
    expect(formatBytes(1536, 2)).toBe('1.5 KB'); // toFixed(2) but parseFloat removes trailing zeros
    expect(formatBytes(1540, 2)).toBe('1.5 KB'); // 1540 / 1024 = 1.5039... -> 1.5
    expect(formatBytes(1550, 2)).toBe('1.51 KB'); // 1550 / 1024 = 1.5136... -> 1.51
  });
});
