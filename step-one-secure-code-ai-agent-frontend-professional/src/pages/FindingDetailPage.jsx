import { useNavigate, useParams } from 'react-router-dom';
import { getWorkbench } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import StatusBadge from '../components/StatusBadge';
import UpdatedFileDownload from '../components/UpdatedFileDownload';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

function severityTone(severity) {
  if (severity === 'Critical') return 'danger';
  if (severity === 'High') return 'warning';
  return 'info';
}

function severityLabel(severity, ar) {
  if (!ar) return severity;
  if (severity === 'Critical') return 'حرجة';
  if (severity === 'High') return 'عالية';
  return 'متوسطة';
}

export default function FindingDetailPage() {
  const navigate = useNavigate();
  const { projectId, findingId } = useParams();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data, error, loading, reload } = useAsyncResource(getWorkbench, []);
  const finding = data?.findings.find((item) => item.id === findingId) ?? null;
  const file = finding ? data?.files.find((item) => item.id === finding.fileId) : null;

  return (
    <AppShell>
      <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل تفاصيل النتيجة…' : 'Loading finding detail…'} onRetry={reload} />

      {!loading && !error && data && !finding ? (
        <section className="empty-panel">
          <strong>{ar ? 'لم يتم العثور على النتيجة.' : 'Finding not found.'}</strong>
          <button className="button button-secondary" onClick={() => navigate(`/projects/${projectId}/findings`)} type="button">
            {ar ? 'العودة للنتائج' : 'Back to findings'}
          </button>
        </section>
      ) : null}

      {!loading && !error && finding && file ? (
        <article className="finding-detail-page">
          <header className="finding-detail-header">
            <div>
              <button className="text-link detail-back" onClick={() => navigate(`/projects/${projectId}/findings`)} type="button">
                {ar ? 'النتائج' : 'Findings'}
              </button>
              <div className="finding-id-row">
                <span className="technical-value">{finding.id}</span>
                <StatusBadge tone={severityTone(finding.severity)}>{severityLabel(finding.severity, ar)}</StatusBadge>
                <StatusBadge tone={finding.verification.closure === 'Verified remediated' ? 'success' : 'neutral'}>
                  {ar
                    ? finding.verification.closure === 'Verified remediated' ? 'تم التحقق من المعالجة' : 'تحتاج تحقق'
                    : finding.verification.closure}
                </StatusBadge>
              </div>
              <h1>{ar ? finding.titleAr ?? finding.title : finding.title}</h1>
              <p className="technical-value">{file.path} · line {finding.line} · {finding.cwe}</p>
            </div>
            <button className="button button-primary" onClick={() => navigate(`/projects/${projectId}/workbench`)} type="button">
              {ar ? 'فتحها في Workbench' : 'Open in workbench'}
            </button>
          </header>

          <section className="finding-detail-section">
            <span className="section-label">{ar ? 'ما الذي تم اكتشافه' : 'WHAT WAS DETECTED'}</span>
            <h2>{ar ? 'السبب الجذري' : 'Root cause'}</h2>
            <p>{ar ? finding.rootCauseAr ?? finding.rootCause : finding.rootCause}</p>
          </section>

          <section className="finding-detail-grid">
            <article>
              <span className="section-label">{ar ? 'الدليل' : 'EVIDENCE'}</span>
              <p>{ar ? finding.evidenceAr ?? finding.evidence : finding.evidence}</p>
            </article>
            <article>
              <span className="section-label">{ar ? 'السياق الأمني' : 'SECURITY CONTEXT'}</span>
              <dl className="detail-definition-list">
                <div><dt>Source</dt><dd className="technical-value">{finding.source}</dd></div>
                <div><dt>Sink</dt><dd className="technical-value">{finding.sink}</dd></div>
                <div><dt>Standard</dt><dd className="technical-value technical-wrap">{finding.standard}</dd></div>
              </dl>
            </article>
          </section>

          <section className="finding-detail-section">
            <span className="section-label">TRACE</span>
            <div className="trace-path" dir="ltr">
              {finding.trace.map((item, index) => (
                <span key={item}>{item}{index < finding.trace.length - 1 ? <b>→</b> : null}</span>
              ))}
            </div>
          </section>

          <section className="finding-detail-section code-evidence-section">
            <div className="section-heading-inline">
              <div>
                <span className="section-label">{ar ? 'الكود الحالي' : 'CURRENT CODE'}</span>
                <h2>{ar ? 'السطر المتأثر والسياق القريب' : 'Affected code and nearby context'}</h2>
              </div>
              <span className="technical-value">{file.path}</span>
            </div>
            <pre className="detail-code" dir="ltr">{finding.weakCode}</pre>
          </section>

          <section className="finding-detail-section code-evidence-section">
            <span className="section-label">{ar ? 'التغيير المقترح' : 'PROPOSED SECURE CHANGE'}</span>
            <h2>{ar ? 'Secure Candidate — يحتاج تحقق' : 'Secure Candidate — verification required'}</h2>
            <div className="detail-diff" dir="ltr">
              <div><span>ORIGINAL</span><pre>{finding.weakCode}</pre></div>
              <div><span>UPDATED</span><pre>{finding.secureCode}</pre></div>
            </div>
          </section>

          <section className="finding-detail-section">
            <span className="section-label">{ar ? 'التحقق' : 'VERIFICATION'}</span>
            <div className="verification-list detail-verification-list">
              {Object.entries(finding.verification).map(([key, value]) => (
                <div className="verification-row" key={key}>
                  <span className="technical-value">{key}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="finding-detail-section artifact-section">
            <UpdatedFileDownload ar={ar} finding={finding} />
          </section>
        </article>
      ) : null}
    </AppShell>
  );
}
