import { expect, test } from 'vitest';
import { api } from '../../../src/ravioli/frontend/src/services/api';

test('api service is syntactically valid and exportable', () => {
  expect(api).toBeDefined();
  expect(typeof api.listAnalyses).toBe('function');
  expect(typeof api.generateQuickInsight).toBe('function');
});
