import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { createRepairProposal, findingLifecycleUrl, getFindingLifecycle, getRepairEvidence, getStoredAnalysis } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';
import { locateFinding } from '../workspace/locateFinding';

function EvidenceSection({ label, title, children, unavailable = false }) {
  return <section className={`evidence-section${unavailable ? ' unavailable' : ''}`} id={`evidence-${label.toLowerCase().replaceAll(' ', '-')}`}><span>{label}</span><h2>{title}</h2><div>{children}</div></section>;
}

function FindingStageRail({ stages, ar }) {
  const targets = { UNDERSTAND: 'where', VERIFY: 'verification', PATCH: 'fix', FUNCTIONAL_TEST: 'tests', REPLAY: 'runtime', RE_SCAN_RE_TRACE: 're-verify', CLOSURE: 'evidence' };
  return <aside className="finding-stage-rail" aria-label={ar ? 'مراحل الدليل الحالية' : 'Current evidence stages'}>
    <strong>{ar ? 'حالة المراحل' : 'Stage status'}</strong>
    <p>{ar ? 'من السجل الحقيقي لهذه النتيجة' : 'From this finding’s saved record'}</p>
    <ol>{stages.map(({ id, status }) => <li key={id}><button className={['OBSERVED', 'STATICALLY_SUPPORTED', 'PROPOSED_UNVERIFIED', 'PASS'].includes(status) ? 'stage-observed' : 'stage-limited'} onClick={() => document.getElementById(`evidence-${targets[id] ?? id.toLowerCase().replaceAll('_', '-')}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })} type="button"><span>{id.replaceAll('_', ' ')}</span><small>{status.replaceAll('_', ' ')}</small></button></li>)}</ol>
  </aside>;
}

function TraceFlow({ steps = [], ar, canPropose }) {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(steps.length);
      return undefined;
    }
    setVisible(0);
    if (!steps.length) return undefined;
    let shown = 0;
    const timer = window.setInterval(() => {
      shown += 1;
      setVisible(shown);
      if (shown >= steps.length) window.clearInterval(timer);
    }, 420);
    return () => window.clearInterval(timer);
  }, [steps]);

  if (!steps.length) return <strong>UNRESOLVED</strong>;
  return <div className="trace-flow">
    <ol className="evidence-trace" aria-label={ar ? 'خطوات التتبع المثبتة' : 'Observed trace steps'}>
      {steps.map((step, index) => <li className={index < visible ? 'trace-visible' : 'trace-pending'} key={`${step.kind}-${index}`}>
        <b>{step.kind}</b><code dir="ltr">{step.target ?? step.value ?? 'Unresolved'} · line {step.line ?? '?'}</code>
      </li>)}
    </ol>
    {visible === steps.length && <div className="trace-next" role="status">
      <span>{ar ? 'انتهى عرض المسار الساكن المرصود؛ لم يُثبت استغلال فعلي.' : 'Observed static path shown; exploitability remains unverified.'}</span>
      {canPropose && <button className="button button-secondary compact-button" onClick={() => document.getElementById('repair-proposal')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' })} type="button">{ar ? 'افحص الإصلاح المقترح' : 'Review proposed repair'}</button>}
    </div>}
  </div>;
}

function ProposalDiff({ diff }) {
  return <div className="repair-proposal-result"><pre dir="ltr" aria-label="Proposed patch diff"><code>{diff.split('\n').map((line, index) => <span className={`diff-line ${line.startsWith('+') && !line.startsWith('+++') ? 'diff-added' : line.startsWith('-') && !line.startsWith('---') ? 'diff-removed' : line.startsWith('@@') ? 'diff-location' : ''}`} key={index} style={{ '--diff-order': Math.min(index, 12) }}>{line}{'\n'}</span>)}</code></pre></div>;
}

export default function FindingDetailPage() {
  const navigate = useNavigate();
  const { projectId, findingId } = useParams();
  const [searchParams] = useSearchParams();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [originalFile, setOriginalFile] = useState(null);
  const [proposal, setProposal] = useState(null);
  const [repairError, setRepairError] = useState('');
  const [repairBusy, setRepairBusy] = useState(false);
  const { data, error, loading, reload } = useAsyncResource(() => getStoredAnalysis(projectId), [projectId]);
  const { data: savedRepair, reload: reloadRepair } = useAsyncResource(() => getRepairEvidence(projectId, findingId), [projectId, findingId]);
  const fileSelector = searchParams.get('file');
  const { data: lifecycleResponse, error: lifecycleError, reload: reloadLifecycle } = useAsyncResource(() => getFindingLifecycle(projectId, findingId, fileSelector), [projectId, findingId, fileSelector]);
  const lifecycle = lifecycleResponse?.lifecycle;
  const result = data?.record?.result;
  const match = result ? locateFinding(result, findingId, searchParams.get('file')) : null;
  const finding = match?.finding;
  const storedProposal = savedRepair?.saved_evidence?.evidence;
  const activeProposal = proposal?.finding_id === finding?.id ? proposal : storedProposal?.finding_id === finding?.id ? storedProposal : null;
  const path = match?.file?.artifact?.relative_path ?? match?.file?.artifact?.filename ?? 'Unknown';

  async function requestProposal(event) {
    event.preventDefault();
    if (!originalFile || !finding) return;
    setRepairBusy(true);
    setRepairError('');
    setProposal(null);
    try {
      const response = await createRepairProposal({ analysisId: projectId, findingId: finding.id, file: originalFile });
      setProposal(response.proposal);
      reloadRepair();
      reloadLifecycle();
    } catch (failure) {
      setRepairError(failure instanceof Error ? failure.message : 'Repair proposal unavailable.');
    } finally {
      setRepairBusy(false);
    }
  }

  return <AppShell><section className="evidence-page">
    <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل الدليل المحفوظ…' : 'Loading saved evidence…'} onRetry={reload} />
    {!loading && !error && !match && <div className="empty-panel">{ar ? 'النتيجة غير موجودة أو معرّفها غير فريد. افتحها من قائمة الملفات.' : 'Finding not found or its ID is ambiguous. Open it from the file list.'}</div>}
    {match && <>
      {lifecycleError && <p className="form-error" role="alert">{ar ? 'تعذر تحميل حالة المراحل من الخادم: ' : 'Could not load lifecycle from the server: '}{lifecycleError.message}</p>}
      <header className="evidence-header"><button className="text-link" onClick={() => navigate(`/projects/${projectId}/findings`)} type="button">← {ar ? 'كل النتائج' : 'All findings'}</button><span className="candidate-state">{lifecycle?.finding_status ?? 'LOADING'} · {lifecycle?.closure?.status ?? 'LOADING'}</span><h1>{finding.pack_assessment?.pack?.replaceAll('_', ' ') ?? finding.sink?.category}</h1><p dir="ltr">{path} · {finding.scope?.function ?? 'Unresolved'}() · Line {finding.sink?.start_line ?? 'Unknown'}</p></header>
      <div className="finding-evidence-layout">
      <FindingStageRail ar={ar} stages={lifecycle?.stages ?? []} />
      <div className="finding-evidence-main">
      {['sql_execution_candidate', 'process_execution'].includes(finding.sink?.category) && <section className="repair-proposal-panel" id="repair-proposal" aria-label={ar ? 'توليد إصلاح مقترح' : 'Generate a repair proposal'}>
        <div><span className="eyebrow">{lifecycle?.patch?.status ?? 'LOADING'}</span><h2>{ar ? 'ولّد إصلاحًا مقترحًا' : 'Generate a proposed repair'}</h2><p>{ar ? 'أعد اختيار الملف الأصلي نفسه. نتحقق من بصمته ونولّد تعديلًا محدودًا دون تشغيله أو تغيير الأصل.' : 'Select the exact original again. We verify its digest and generate a narrow patch without running or overwriting it.'}</p></div>
        <form onSubmit={requestProposal}><label htmlFor="repair-original-file">{ar ? 'الملف الأصلي' : 'Original file'}</label><input accept=".py" id="repair-original-file" onChange={(event) => { setOriginalFile(event.target.files?.[0] ?? null); setProposal(null); setRepairError(''); }} required type="file" /><button className="button button-primary" disabled={repairBusy || !originalFile} type="submit">{repairBusy ? (ar ? 'جارٍ توليد المقترح…' : 'Generating…') : (ar ? 'ولّد الإصلاح' : 'Generate proposal')}</button></form>
        {repairError && <p className="form-error" role="alert">{repairError}</p>}
        {activeProposal && <p role="status">{ar ? 'دليل الإصلاح المقترح محفوظ. راجع الفرق وبوابات الإغلاق أدناه.' : 'Proposed repair evidence is saved. Review the diff and closure gates below.'}</p>}
      </section>}
      <div className="evidence-sequence">
        <EvidenceSection label="WHERE" title={ar ? 'وين المشكلة؟' : 'Where?'}><code dir="ltr">{finding.sink?.target ?? 'Unknown'} · {path}:{finding.sink?.start_line ?? '?'}</code></EvidenceSection>
        <EvidenceSection label="WHY" title={ar ? 'ليش اعتُبرت مرشحًا؟' : 'Why a candidate?'}><p>{finding.root_cause?.statement ?? 'Unresolved'}</p><small>{finding.pack_assessment?.basis ?? finding.evidence_strength}</small></EvidenceSection>
        <EvidenceSection label="TRACE" title={ar ? 'مسار البيانات المرصود' : 'Observed data path'}><TraceFlow ar={ar} canPropose={['sql_execution_candidate', 'process_execution'].includes(finding.sink?.category)} key={finding.id} steps={finding.trace} /></EvidenceSection>
        <EvidenceSection label="CODE" title={ar ? 'مقاطع الكود المحفوظة' : 'Saved code excerpts'}><div className="code-evidence-grid">{['source', 'sink'].map((kind) => <div key={kind}><strong>{kind.toUpperCase()} · {path}</strong><pre dir="ltr"><code>{finding.code_evidence?.[kind]?.length ? finding.code_evidence[kind].map((row) => `${row.line}  ${row.text}${row.truncated ? ' …' : ''}`).join('\n') : 'Excerpt unavailable for this saved record.'}</code></pre></div>)}</div></EvidenceSection>
        <EvidenceSection label="VERIFICATION" title={ar ? 'هل تم إثباتها؟' : 'Verified?'}><strong>{lifecycle?.runtime_before?.status ?? 'LOADING'}</strong><p>{ar ? 'المسار الساكن لا يثبت قابلية الاستغلال.' : 'A static path does not prove exploitability.'}</p></EvidenceSection>
        <EvidenceSection label="ROOT CAUSE" title={ar ? 'السبب الجذري' : 'Root cause'}><strong>{lifecycle?.stages?.find((stage) => stage.id === 'ROOT_CAUSE')?.status ?? 'LOADING'}</strong><p>{lifecycle?.root_cause?.explanation ?? lifecycle?.root_cause?.statement ?? 'Unresolved'}</p>{lifecycle?.root_cause?.category && <code dir="ltr">{lifecycle.root_cause.category} · {lifecycle.root_cause.source_location?.line ?? '?'} → {lifecycle.root_cause.sink_location?.line ?? '?'}</code>}</EvidenceSection>
        <EvidenceSection label="FIX" title={ar ? 'الإصلاح' : 'Fix'} unavailable={!activeProposal}><strong>{lifecycle?.patch?.status ?? 'LOADING'}</strong>{activeProposal ? <><p>{ar ? 'التعديل على نسخة منفصلة؛ الاختبار التشغيلي يحتاج عزلًا ولم يُنفّذ.' : 'The patch is a separate copy; runtime testing requires isolation and was not run.'}</p><code dir="ltr">{activeProposal.original_sha256} → {activeProposal.updated_sha256}</code>{lifecycle?.patch?.download_available && <a className="button button-secondary" href={findingLifecycleUrl(projectId, findingId, path, 'patched')}>{ar ? 'تنزيل الملف المعدّل' : 'Download patched file'}</a>}</> : <p>{ar ? 'أعد رفع الأصل في الأعلى لتوليد تعديل مدعوم لهذا النمط.' : 'Re-upload the original above to generate a supported patch.'}</p>}</EvidenceSection>
        <EvidenceSection label="DIFF" title={ar ? 'قبل / بعد' : 'Before / after'} unavailable={!activeProposal}>{activeProposal ? <ProposalDiff diff={activeProposal.diff} /> : <strong>NOT AVAILABLE</strong>}</EvidenceSection>
        <EvidenceSection label="TESTS" title={ar ? 'اختبار الوظيفة' : 'Functional tests'} unavailable><strong>{lifecycle?.functional_test?.status ?? 'LOADING'}</strong><p>{lifecycle?.functional_test?.reason}</p></EvidenceSection>
        <EvidenceSection label="RE-VERIFY" title={ar ? 'إعادة الفحص والتتبع' : 'Re-scan and re-trace'} unavailable={!lifecycle?.re_scan?.status}><strong className={`rescan-state ${lifecycle?.re_scan?.status === 'NO_MATCH_OBSERVED' ? 'rescan-clear' : lifecycle?.re_scan?.status ? 'rescan-alert' : ''}`}>STATIC RE-SCAN: {lifecycle?.re_scan?.status ?? 'LOADING'}</strong><p>STATIC RE-TRACE: {lifecycle?.re_trace?.status ?? 'LOADING'}</p>{lifecycle?.re_trace?.after_paths?.map((item, index) => <p key={index} dir="ltr">{item.assessment.pack}: {item.assessment.basis} · {item.trace.map((step) => step.target || step.via || step.kind).join(' → ')}</p>)}<p>{ar ? 'إعادة التشغيل وإعادة تتبع السلوك الفعلي لم تُنفذا.' : 'Runtime replay and behavioral re-trace were not run.'}</p></EvidenceSection>
        <EvidenceSection label="RUNTIME" title={ar ? 'التحقق المعزول وReplay' : 'Isolated verification and replay'} unavailable><strong>{lifecycle?.replay_after?.status ?? 'LOADING'}</strong><p>{ar ? 'لا يوجد منفّذ عزل معتمد. لم يُشغّل المشروع المرفوع أو سيناريو استغلال.' : 'No reviewed isolated executor. The uploaded project and exploit scenario were not run.'}</p></EvidenceSection>
        <EvidenceSection label="CLOSURE GATES" title={ar ? 'بوابات الإغلاق' : 'Closure gates'} unavailable={!activeProposal}><strong>{lifecycle?.closure?.status ?? 'LOADING'}</strong>{lifecycle?.closure?.gates?.length > 0 && <ul className="closure-gates">{lifecycle.closure.gates.map((gate) => <li key={gate.name}><span>{gate.name.replaceAll('_', ' ')}</span><b>{gate.status}</b></li>)}</ul>}</EvidenceSection>
        <EvidenceSection label="EVIDENCE" title={ar ? 'دليل الإغلاق' : 'Closure evidence'} unavailable><strong>{lifecycle?.closure?.status ?? 'LOADING'}</strong>{lifecycle && <a className="button button-secondary" href={findingLifecycleUrl(projectId, findingId, path, 'report')}>{ar ? 'تنزيل تقرير الأمان' : 'Download security report'}</a>}</EvidenceSection>
      </div>
      </div>
      </div>
    </>}
  </section></AppShell>;
}
