import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { getStoredAnalysis } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';
import { locateFinding } from '../workspace/locateFinding';

function EvidenceSection({ label, title, children, unavailable = false }) {
  return <section className={`evidence-section${unavailable ? ' unavailable' : ''}`}><span>{label}</span><h2>{title}</h2><div>{children}</div></section>;
}

export default function FindingDetailPage() {
  const navigate = useNavigate();
  const { projectId, findingId } = useParams();
  const [searchParams] = useSearchParams();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data, error, loading, reload } = useAsyncResource(() => getStoredAnalysis(projectId), [projectId]);
  const result = data?.record?.result;
  const match = result ? locateFinding(result, findingId, searchParams.get('file')) : null;
  const finding = match?.finding;
  const path = match?.file?.artifact?.relative_path ?? match?.file?.artifact?.filename ?? 'Unknown';

  return <AppShell><section className="evidence-page">
    <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل الدليل المحفوظ…' : 'Loading saved evidence…'} onRetry={reload} />
    {!loading && !error && !match && <div className="empty-panel">{ar ? 'النتيجة غير موجودة أو معرّفها غير فريد. افتحها من قائمة الملفات.' : 'Finding not found or its ID is ambiguous. Open it from the file list.'}</div>}
    {match && <>
      <header className="evidence-header"><button className="text-link" onClick={() => navigate(`/projects/${projectId}/findings`)} type="button">← {ar ? 'كل النتائج' : 'All findings'}</button><span className="candidate-state">CANDIDATE · NOT VERIFIED</span><h1>{finding.pack_assessment?.pack?.replaceAll('_', ' ') ?? finding.sink?.category}</h1><p dir="ltr">{path} · {finding.scope?.function ?? 'Unresolved'}() · Line {finding.sink?.start_line ?? 'Unknown'}</p></header>
      <div className="evidence-sequence">
        <EvidenceSection label="WHERE" title={ar ? 'وين المشكلة؟' : 'Where?'}><code dir="ltr">{finding.sink?.target ?? 'Unknown'} · {path}:{finding.sink?.start_line ?? '?'}</code></EvidenceSection>
        <EvidenceSection label="WHY" title={ar ? 'ليش اعتُبرت مرشحًا؟' : 'Why a candidate?'}><p>{finding.root_cause?.statement ?? 'Unresolved'}</p><small>{finding.pack_assessment?.basis ?? finding.evidence_strength}</small></EvidenceSection>
        <EvidenceSection label="TRACE" title={ar ? 'مسار البيانات المرصود' : 'Observed data path'}><ol className="evidence-trace">{finding.trace?.map((step, index) => <li key={`${step.kind}-${index}`}><b>{step.kind}</b><code dir="ltr">{step.target ?? step.value ?? 'Unresolved'} · line {step.line ?? '?'}</code></li>)}</ol></EvidenceSection>
        <EvidenceSection label="CODE" title={ar ? 'مقاطع الكود المحفوظة' : 'Saved code excerpts'}><div className="code-evidence-grid">{['source', 'sink'].map((kind) => <div key={kind}><strong>{kind.toUpperCase()} · {path}</strong><pre dir="ltr"><code>{finding.code_evidence?.[kind]?.length ? finding.code_evidence[kind].map((row) => `${row.line}  ${row.text}${row.truncated ? ' …' : ''}`).join('\n') : 'Excerpt unavailable for this saved record.'}</code></pre></div>)}</div></EvidenceSection>
        <EvidenceSection label="VERIFICATION" title={ar ? 'هل تم إثباتها؟' : 'Verified?'}><strong>{finding.exploitability?.status ?? 'UNVERIFIED'}</strong><p>{ar ? 'المسار الساكن لا يثبت قابلية الاستغلال.' : 'A static path does not prove exploitability.'}</p></EvidenceSection>
        <EvidenceSection label="ROOT CAUSE" title={ar ? 'السبب الجذري' : 'Root cause'}><strong>{finding.root_cause?.status ?? 'UNRESOLVED'}</strong><p>{finding.root_cause?.statement ?? 'Unresolved'}</p></EvidenceSection>
        <EvidenceSection label="FIX" title={ar ? 'الإصلاح' : 'Fix'} unavailable><strong>{finding.remediation?.status ?? 'NOT_PROPOSED'}</strong><p>{ar ? 'لا يوجد إصلاح معتمد قبل التحقق من المشكلة.' : 'No approved fix before exploitability verification.'}</p></EvidenceSection>
        <EvidenceSection label="DIFF" title={ar ? 'قبل / بعد' : 'Before / after'} unavailable><strong>NOT AVAILABLE</strong></EvidenceSection>
        <EvidenceSection label="TESTS" title={ar ? 'اختبار الوظيفة' : 'Functional tests'} unavailable><strong>NOT RUN</strong></EvidenceSection>
        <EvidenceSection label="RE-VERIFY" title={ar ? 'إعادة الفحص والتتبع' : 'Re-scan and re-trace'} unavailable><strong>NOT RUN</strong></EvidenceSection>
        <EvidenceSection label="EVIDENCE" title={ar ? 'دليل الإغلاق' : 'Closure evidence'} unavailable><strong>{finding.closure?.status ?? 'NOT_AVAILABLE'}</strong></EvidenceSection>
      </div>
    </>}
  </section></AppShell>;
}
