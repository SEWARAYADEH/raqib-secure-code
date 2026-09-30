import assert from 'node:assert/strict';
import test from 'node:test';
import { locateFinding } from './locateFinding.js';

test('identical finding IDs across files require the file path', () => {
  const first = { artifact: { relative_path: 'api/routes.py' }, security_analysis: { candidates: [{ id: 'same' }] } };
  const second = { artifact: { relative_path: 'admin/routes.py' }, security_analysis: { candidates: [{ id: 'same' }] } };
  const result = { files: [first, second] };

  assert.equal(locateFinding(result, 'same', null), null);
  assert.equal(locateFinding(result, 'same', 'admin/routes.py')?.file, second);
  assert.equal(locateFinding(result, 'same', 'other/routes.py'), null);
});

test('a unique file finding remains accessible without a path', () => {
  const result = { artifact: { filename: 'app.py' }, security_analysis: { candidates: [{ id: 'unique' }] } };
  assert.equal(locateFinding(result, 'unique', null)?.file, result);
});
