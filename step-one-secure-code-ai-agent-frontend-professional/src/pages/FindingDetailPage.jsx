import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { createRepairProposal, getRepairEvidence, getStoredAnalysis } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';
import { locateFinding } from '../workspace/locateFinding';

function EvidenceSection({ label, title, children, unavailable = false }) {
  return <section className={`evidence-section${unavailable ? ' unavailable' : ''}`}><span>{label}</span><h2>{title}</h2><div>{children}</div></section>;
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

function downloadProposal(proposal) {
  const blob = new Blob([proposal.updated_source], { type: 'text/x-python;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = proposal.filename.replace(/\.py$/i, '') + '.proposed.py';
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
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
      <header className="evidence-header"><button className="text-link" onClick={() => navigate(`/projects/${projectId}/findings`)} type="button">← {ar ? 'كل النتائج' : 'All findings'}</button><span className="candidate-state">STATIC_CANDIDATE · {activeProposal?.closure_evaluation?.status ?? 'NOT VERIFIED'}</span><h1>{finding.pack_assessment?.pack?.replaceAll('_', ' ') ?? finding.sink?.category}</h1><p dir="ltr">{path} · {finding.scope?.function ?? 'Unresolved'}() · Line {finding.sink?.start_line ?? 'Unknown'}</p></header>
      {['sql_execution_candidate', 'process_execution'].includes(finding.sink?.category) && <section className="repair-proposal-panel" id="repair-proposal" aria-label={ar ? 'توليد إصلاح مقترح' : 'Generate a repair proposal'}>
        <div><span className="eyebrow">PROPOSED · UNVERIFIED</span><h2>{ar ? 'ولّد إصلاحًا مقترحًا' : 'Generate a proposed repair'}</h2><p>{ar ? 'أعد اختيار الملف الأصلي نفسه. نتحقق من بصمته ونولّد تعديلًا محدودًا دون تشغيله أو تغيير الأصل.' : 'Select the exact original again. We verify its digest and generate a narrow patch without running or overwriting it.'}</p></div>
        <form onSubmit={requestProposal}><label htmlFor="repair-original-file">{ar ? 'الملف الأصلي' : 'Original file'}</label><input accept=".py" id="repair-original-file" onChange={(event) => { setOriginalFile(event.target.files?.[0] ?? null); setProposal(null); setRepairError(''); }} required type="file" /><button className="button button-primary" disabled={repairBusy || !originalFile} type="submit">{repairBusy ? (ar ? 'جارٍ توليد المقترح…' : 'Generating…') : (ar ? 'ولّد الإصلاح' : 'Generate proposal')}</button></form>
        {repairError && <p className="form-error" role="alert">{repairError}</p>}
        {activeProposal && <p role="status">{ar ? 'دليل الإصلاح المقترح محفوظ. راجع الفرق وبوابات الإغلاق أدناه.' : 'Proposed repair evidence is saved. Review the diff and closure gates below.'}</p>}
      </section>}
      <div className="evidence-sequence">
        <EvidenceSection label="WHERE" title={ar ? 'وين المشكلة؟' : 'Where?'}><code dir="ltr">{finding.sink?.target ?? 'Unknown'} · {path}:{finding.sink?.start_line ?? '?'}</code></EvidenceSection>
        <EvidenceSection label="WHY" title={ar ? 'ليش اعتُبرت مرشحًا؟' : 'Why a candidate?'}><p>{finding.root_cause?.statement ?? 'Unresolved'}</p><small>{finding.pack_assessment?.basis ?? finding.evidence_strength}</small></EvidenceSection>
        <EvidenceSection label="TRACE" title={ar ? 'مسار البيانات المرصود' : 'Observed data path'}><TraceFlow ar={ar} canPropose={['sql_execution_candidate', 'process_execution'].includes(finding.sink?.category)} key={finding.id} steps={finding.trace} /></EvidenceSection>
        <EvidenceSection label="CODE" title={ar ? 'مقاطع الكود المحفوظة' : 'Saved code excerpts'}><div className="code-evidence-grid">{['source', 'sink'].map((kind) => <div key={kind}><strong>{kind.toUpperCase()} · {path}</strong><pre dir="ltr"><code>{finding.code_evidence?.[kind]?.length ? finding.code_evidence[kind].map((row) => `${row.line}  ${row.text}${row.truncated ? ' …' : ''}`).join('\n') : 'Excerpt unavailable for this saved record.'}</code></pre></div>)}</div></EvidenceSection>
        <EvidenceSection label="VERIFICATION" title={ar ? 'هل تم إثباتها؟' : 'Verified?'}><strong>{finding.exploitability?.status ?? 'UNVERIFIED'}</strong><p>{ar ? 'المسار الساكن لا يثبت قابلية الاستغلال.' : 'A static path does not prove exploitability.'}</p></EvidenceSection>
        <EvidenceSection label="ROOT CAUSE" title={ar ? 'السبب الجذري' : 'Root cause'}><strong>{activeProposal?.root_cause?.status ?? finding.root_cause?.status ?? 'UNRESOLVED'}</strong><p>{activeProposal?.root_cause?.explanation ?? finding.root_cause?.statement ?? 'Unresolved'}</p>{activeProposal?.root_cause && <code dir="ltr">{activeProposal.root_cause.category} · {activeProposal.root_cause.source_location.line} → {activeProposal.root_cause.sink_location.line}</code>}</EvidenceSection>
        <EvidenceSection label="FIX" title={ar ? 'الإصلاح' : 'Fix'} unavailable={!activeProposal}><strong>{activeProposal?.status ?? finding.remediation?.status ?? 'NOT_PROPOSED'}</strong>{activeProposal ? <><p>{ar ? 'التعديل على نسخة منفصلة، دون الكتابة فوق الأصل. إثبات سلامة الوظيفة أدناه محصور في Fixture موثوق إذا توفر.' : 'The patch is a separate copy. Any functional proof below is limited to the pinned trusted fixture.'}</p><code dir="ltr">{activeProposal.original_sha256} → {activeProposal.updated_sha256}</code>{activeProposal.updated_source && <button className="button button-secondary" onClick={() => downloadProposal(activeProposal)} type="button">{ar ? 'تنزيل النسخة المقترحة' : 'Download proposed file'}</button>}</> : <p>{ar ? 'أعد رفع الأصل في الأعلى لتوليد تعديل مدعوم لهذا النمط.' : 'Re-upload the original above to generate a supported patch.'}</p>}</EvidenceSection>
        <EvidenceSection label="DIFF" title={ar ? 'قبل / بعد' : 'Before / after'} unavailable={!activeProposal}>{activeProposal ? <ProposalDiff diff={activeProposal.diff} /> : <strong>NOT AVAILABLE</strong>}</EvidenceSection>
        <EvidenceSection label="TESTS" title={ar ? 'اختبار الوظيفة' : 'Functional tests'} unavailable={!activeProposal?.functional_evidence || activeProposal.functional_evidence.status === 'NOT_AVAILABLE'}><strong>{activeProposal?.functional_evidence?.status ?? 'NOT_AVAILABLE'}</strong>{activeProposal?.functional_evidence && <p dir="ltr">{activeProposal.functional_evidence.scope ?? 'UNTRUSTED_PROJECT'} · {activeProposal.functional_evidence.test_id ?? activeProposal.functional_evidence.reason}</p>}</EvidenceSection>
        <EvidenceSection label="RE-VERIFY" title={ar ? 'إعادة الفحص والتتبع' : 'Re-scan and re-trace'} unavailable={!activeProposal}><strong>{activeProposal ? `STATIC RE-SCAN: ${activeProposal.static_reanalysis.status}` : 'NOT RUN'}</strong>{activeProposal && <><p>STATIC RE-TRACE: {activeProposal.static_retrace.status}</p>{activeProposal.static_retrace.after_paths.map((item, index) => <p key={index} dir="ltr">{item.assessment.pack}: {item.assessment.basis} · {item.trace.map((step) => step.target || step.via || step.kind).join(' → ')}</p>)}</>}<p>{ar ? 'إعادة التشغيل وإعادة تتبع السلوك الفعلي لم تُنفذا.' : 'Runtime replay and behavioral re-trace were not run.'}</p></EvidenceSection>
        <EvidenceSection label="RUNTIME" title={ar ? 'التحقق المعزول وReplay' : 'Isolated verification and replay'} unavailable><strong>NOT_AVAILABLE</strong><p>{ar ? 'لا يوجد منفّذ عزل معتمد. لم يُشغّل المشروع المرفوع أو سيناريو استغلال.' : 'No reviewed isolated executor. The uploaded project and exploit scenario were not run.'}</p></EvidenceSection>
        <EvidenceSection label="CLOSURE GATES" title={ar ? 'بوابات الإغلاق' : 'Closure gates'} unavailable={!activeProposal}><strong>{activeProposal?.closure_evaluation?.status ?? 'NOT_AVAILABLE'}</strong>{activeProposal?.closure_evaluation && <ul className="closure-gates">{activeProposal.closure_evaluation.gates.map((gate) => <li key={gate.name}><span>{gate.name.replaceAll('_', ' ')}</span><b>{gate.status}</b></li>)}</ul>}</EvidenceSection>
        <EvidenceSection label="EVIDENCE" title={ar ? 'دليل الإغلاق' : 'Closure evidence'} unavailable><strong>{activeProposal?.closure_evaluation?.verified_closed ? 'VERIFIED_CLOSED' : 'NOT_AVAILABLE'}</strong></EvidenceSection>
      </div>
    </>}
  </section></AppShell>;
}
