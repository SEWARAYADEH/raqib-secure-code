export function buildReport(record) {
  if (!record?.result || !record?.analysis_id || record.integrity !== 'HMAC-SHA256') {
    throw new Error('A verified persisted analysis record is required.');
  }

  const result = record.result;
  const files = result.files ?? [result];
  const findings = files.flatMap((file) => (
    (file.security_analysis?.candidates ?? []).map((candidate) => ({
      id: candidate.id,
      file: file.artifact?.relative_path ?? file.artifact?.filename ?? 'UNKNOWN',
      state: candidate.state,
      title: candidate.title,
      standards: candidate.standards,
      source: candidate.source,
      sink: candidate.sink,
      trace: candidate.trace,
      reachability: candidate.reachability,
      exploitability: candidate.exploitability,
      controls: candidate.controls,
      code_evidence: candidate.code_evidence ?? null,
    }))
  )).concat((result.files ? result.security_analysis?.candidates ?? [] : []).map((candidate) => ({
    id: candidate.id,
    file: `${candidate.cross_file?.source_file ?? 'UNKNOWN'} → ${candidate.cross_file?.target_file ?? 'UNKNOWN'}`,
    state: candidate.state,
    title: candidate.title,
    standards: candidate.standards,
    source: candidate.source,
    sink: candidate.sink,
    trace: candidate.trace,
    reachability: candidate.reachability,
    exploitability: candidate.exploitability,
    controls: candidate.controls,
    code_evidence: candidate.code_evidence ?? null,
  })));
  const nonCandidatePaths = files.flatMap((file) => (
    (file.security_analysis?.non_candidates ?? []).map((item) => ({
      file: file.artifact?.relative_path ?? file.artifact?.filename ?? 'UNKNOWN',
      source: item.source,
      sink: item.sink,
      assessment: item.assessment,
    }))
  ));
  const advisory = result.project_understanding?.dependency_advisories;
  const sources = files.reduce((sum, file) => sum + (file.security_semantics?.counts?.sources ?? 0), 0);
  const sinks = files.reduce((sum, file) => sum + (file.security_semantics?.counts?.sinks ?? 0), 0);
  const observedPaths = files.reduce((sum, file) => sum
    + (file.data_flow?.counts?.observed_paths ?? 0)
    + (file.inter_function_data_flow?.counts?.observed_paths ?? 0), 0)
    + (result.project_understanding?.counts?.observed_cross_file_paths ?? 0);
  const unresolvedPaths = nonCandidatePaths.filter((item) =>
    item.assessment?.status?.includes('UNRESOLVED')).length;

  return {
    schema_version: '1.0',
    report_type: 'PARTIAL_STATIC_EVIDENCE',
    analysis_id: record.analysis_id,
    created_at: record.created_at ?? null,
    generated_from_record_integrity: record.integrity,
    executive: {
      artifact_name: result.artifact?.filename ?? 'UNKNOWN',
      artifact_sha256: record.artifact_sha256,
      scope: result.analysis?.scope ?? 'UNKNOWN',
      analyzed_files: files.length,
      sources,
      sinks,
      observed_paths: observedPaths,
      evidence_traces: findings.filter((finding) => finding.trace?.length > 0).length,
      unresolved_paths: unresolvedPaths,
      finding_candidates: findings.length,
      non_candidate_paths: nonCandidatePaths.length,
      dependency_advisory_matches: advisory?.counts?.advisory_matches ?? 0,
      verified_exploitable: 0,
      verified_closed: 0,
      conclusion: 'Static evidence only; exploitability and closure are unverified.',
    },
    technical: {
      findings,
      non_candidate_paths: nonCandidatePaths,
      dependency_advisories: advisory ?? { status: 'NOT_APPLICABLE' },
      recommendations: [
        'Review each observed path and its controls before deciding whether it is exploitable.',
        'Validate proposed changes and preserve application behavior in an isolated test environment.',
      ],
      limitations: [
        'Supported languages are Python and JavaScript/JSX.',
        'General cross-file data flow and runtime reachability are unresolved.',
        'A candidate or advisory match is not a verified vulnerability.',
      ],
    },
    closure_evidence: {
      status: 'NOT_AVAILABLE',
      functional_test: 'NOT_RUN',
      replay: 'NOT_RUN',
      re_scan: 'NOT_RUN',
      re_trace: 'NOT_RUN',
      closure_decision: 'NOT_ELIGIBLE',
    },
  };
}
