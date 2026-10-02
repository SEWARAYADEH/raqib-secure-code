import assert from 'node:assert/strict';
import test from 'node:test';

import { buildReport } from './buildReport.js';

test('report keeps a candidate separate from verified closure', () => {
  const report = buildReport({
    analysis_id: 'analysis-1',
    created_at: '2026-10-01T00:00:00+00:00',
    artifact_sha256: 'abc',
    integrity: 'HMAC-SHA256',
    result: {
      artifact: { filename: 'sample.py' },
      analysis: { scope: 'FILE' },
      security_semantics: { counts: { sources: 2, sinks: 1 } },
      data_flow: { counts: { observed_paths: 1 } },
      security_analysis: {
        candidates: [{
          id: 'candidate-1', state: 'CANDIDATE', title: 'Observed flow',
          standards: { cwe: 'CWE-89', status: 'CANDIDATE_MAPPING' },
          source: { category: 'http_query_input' },
          sink: { category: 'sql_execution_candidate' },
          trace: [], reachability: {}, exploitability: {}, controls: {},
          code_evidence: { source: [{ line: 5, text: 'request.args.get("id")' }], sink: [] },
        }],
        non_candidates: [{
          source: { category: 'http_query_input' },
          sink: { category: 'sql_execution_candidate' },
          assessment: { status: 'NON_QUERY_ARGUMENT_ONLY' },
        }],
        counts: { non_candidate_paths: 1 },
      },
    },
  });
  assert.equal(report.executive.finding_candidates, 1);
  assert.equal(report.executive.sources, 2);
  assert.equal(report.executive.sinks, 1);
  assert.equal(report.executive.observed_paths, 1);
  assert.equal(report.created_at, '2026-10-01T00:00:00+00:00');
  assert.deepEqual(report.technical.findings[0].code_evidence.source, [{ line: 5, text: 'request.args.get("id")' }]);
  assert.equal(report.executive.non_candidate_paths, 1);
  assert.equal(report.technical.non_candidate_paths[0].assessment.status, 'NON_QUERY_ARGUMENT_ONLY');
  assert.equal(report.executive.verified_closed, 0);
  assert.equal(report.closure_evidence.status, 'NOT_AVAILABLE');
  assert.equal(report.technical.findings[0].standards.status, 'CANDIDATE_MAPPING');
});

test('report rejects unverified in-memory data', () => {
  assert.throws(() => buildReport({ analysis_id: 'x', result: {} }));
});

test('project report includes persisted cross-file findings and paths', () => {
  const candidate = {
    id: 'cross-1', state: 'CANDIDATE', title: 'Cross-file SQL flow',
    cross_file: { source_file: 'routes.py', target_file: 'users.py' },
    standards: { cwe: 'CWE-89' }, source: {}, sink: {}, trace: [{}],
    reachability: {}, exploitability: {}, controls: {},
  };
  const report = buildReport({
    analysis_id: 'analysis-project', artifact_sha256: 'abc', integrity: 'HMAC-SHA256',
    result: {
      artifact: { filename: 'project.zip' }, analysis: { scope: 'PROJECT_STATIC_MODEL' },
      files: [{
        artifact: { relative_path: 'routes.py' },
        security_semantics: { counts: { sources: 1, sinks: 0 } },
        data_flow: { counts: { observed_paths: 0 } },
        inter_function_data_flow: { counts: { observed_paths: 0 } },
        security_analysis: { candidates: [], non_candidates: [] },
      }],
      security_analysis: { candidates: [candidate] },
      project_understanding: { counts: { observed_cross_file_paths: 1 } },
    },
  });
  assert.equal(report.executive.finding_candidates, 1);
  assert.equal(report.executive.observed_paths, 1);
  assert.equal(report.technical.findings[0].file, 'routes.py → users.py');
});
