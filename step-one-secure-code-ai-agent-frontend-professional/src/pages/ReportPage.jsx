import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getStoredAnalysis } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import StatusBadge from '../components/StatusBadge';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';
import { buildReport } from '../report/buildReport';

function downloadReport(report) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `raqib-report-${report.analysis_id}.json`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function ReportPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [section, setSection] = useState('executive');
  const { data, error, loading, reload } = useAsyncResource(
    () => getStoredAnalysis(projectId), [projectId],
  );
  let report = null;
  let reportError = error;
  if (data?.record && !error) {
    try {
      report = buildReport(data.record);
    } catch (failure) {
      reportError = failure;
    }
  }

  return (
    <AppShell>
      <section className="narrow-page configuration-page">
        <div className="page-title-row compact">
          <div>
            <span className="eyebrow">{ar ? 'نتيجة محفوظة ومتحقق من سلامتها' : 'Integrity-checked saved result'}</span>
            <h1>{ar ? 'تقرير رقيب' : 'Raqeeb report'}</h1>
            <p>{ar
              ? 'ثلاث طبقات: ملخص للقرار، تفاصيل للمهندس، وحالة دليل الإغلاق. لا توجد أحكام استغلال أو إغلاق غير مثبتة.'
              : 'Three layers: executive summary, engineering detail, and closure evidence status. No unverified exploit or closure claims.'}</p>
          </div>
        </div>
        <AsyncState error={reportError} loading={loading} loadingLabel={ar ? 'تحميل السجل…' : 'Loading record…'} onRetry={reload} />

        {report && !loading && !reportError ? (
          <>
            <section className="report-toolbar">
              <div className="segmented-control">
                {[
                  ['executive', ar ? 'تنفيذي' : 'Executive'],
                  ['technical', ar ? 'تقني' : 'Technical'],
                  ['closure', ar ? 'دليل الإغلاق' : 'Closure evidence'],
                ].map(([key, label]) => (
                  <button className={section === key ? 'active' : ''} key={key} onClick={() => setSection(key)} type="button">{label}</button>
                ))}
              </div>
              <button className="button button-secondary" onClick={() => downloadReport(report)} type="button">
                <Icon name="report" />{ar ? 'تنزيل JSON' : 'Download JSON'}
              </button>
            </section>

            {section === 'executive' ? (
              <article className="report-document">
                <header className="report-cover">
                  <div><span className="eyebrow">PARTIAL STATIC EVIDENCE</span><h2><bdi dir="ltr">{report.executive.artifact_name}</bdi></h2>
                    <p className="technical-value">Analysis ID · {report.analysis_id}</p>
                    {report.created_at ? <p>{ar ? 'وقت التحليل: ' : 'Analyzed: '}{new Date(report.created_at).toLocaleString()}</p> : null}</div>
                  <StatusBadge tone="warning">UNVERIFIED</StatusBadge>
                </header>
                <section className="report-metrics">
                  <div><span>{ar ? 'ملفات محللة' : 'Analyzed files'}</span><strong>{report.executive.analyzed_files}</strong></div>
                  <div><span>{ar ? 'مدخلات مرصودة' : 'Detected sources'}</span><strong>{report.executive.sources}</strong></div>
                  <div><span>{ar ? 'عمليات حساسة' : 'Detected sinks'}</span><strong>{report.executive.sinks}</strong></div>
                  <div><span>{ar ? 'مرشحات نتائج' : 'Finding candidates'}</span><strong>{report.executive.finding_candidates}</strong></div>
                  <div><span>{ar ? 'مسارات دليل' : 'Evidence traces'}</span><strong>{report.executive.evidence_traces}</strong></div>
                  <div><span>{ar ? 'مسارات غير محسومة' : 'Unresolved paths'}</span><strong>{report.executive.unresolved_paths}</strong></div>
                </section>
                <p>{ar ? 'هذا التقرير يصف الأدلة الساكنة فقط. قابلية الاستغلال والإغلاق لم يُتحقق منهما.' : report.executive.conclusion}</p>
                <p>{ar ? 'بصمة الأصل SHA-256: ' : 'Original SHA-256: '}<code dir="ltr">{report.executive.artifact_sha256}</code></p>
                <h3>{ar ? 'النتائج الأمنية' : 'Security findings'}</h3>
                {report.technical.findings.length ? report.technical.findings.map((item) => <div className="report-finding-row" key={item.id}><StatusBadge tone="warning">STATIC_CANDIDATE</StatusBadge><code dir="ltr">{item.standards?.cwe ?? 'UNRESOLVED'} · {item.file}:{item.sink?.start_line ?? '?'} · {item.sink?.target ?? 'Unknown sink'}</code><button className="button button-secondary" onClick={() => navigate(`/projects/${encodeURIComponent(projectId)}/findings/${encodeURIComponent(item.id)}?${new URLSearchParams({ file: item.file })}`)} type="button">{ar ? 'الدليل والإصلاح' : 'Evidence and repair'}</button></div>) : <p>{ar ? 'لا توجد مرشحات ضمن النطاق المدعوم.' : 'No candidates in supported coverage.'}</p>}
              </article>
            ) : null}

            {section === 'technical' ? (
              <section className="report-document">
                <h2>{ar ? 'النتائج المرشحة وأدلتها' : 'Candidates and evidence'}</h2>
                {report.technical.findings.length ? report.technical.findings.map((item) => (
                  <article className="analysis-path" key={item.id}>
                    <div className="analysis-path-title"><StatusBadge tone="warning">{item.state}</StatusBadge><strong>{item.title}</strong></div>
                    <p><code dir="ltr">{item.file} · {item.standards?.cwe ?? 'UNRESOLVED'} · {item.standards?.status ?? 'UNRESOLVED'}</code></p>
                    <p>{ar ? 'المصدر: ' : 'Source: '}{item.source?.category} → {ar ? 'المصرف: ' : 'Sink: '}{item.sink?.category}</p>
                    <p><code dir="ltr">{item.source?.target ?? 'Unknown source'} · line {item.source?.start_line ?? '?'} → {item.sink?.target ?? 'Unknown sink'} · line {item.sink?.start_line ?? '?'}</code></p>
                    <p>{ar ? 'الوصول أثناء التشغيل: ' : 'Runtime reachability: '}{item.reachability?.runtime_reachability ?? 'UNVERIFIED'} · {ar ? 'قابلية الاستغلال: ' : 'Exploitability: '}{item.exploitability?.status ?? 'UNVERIFIED'}</p>
                    <ol>{(item.trace ?? []).map((step, index) => <li key={`${item.id}:${index}`}><code dir="ltr">{step.kind} · {step.target ?? step.value ?? step.name ?? 'STEP'} · line {step.line ?? '?'}</code></li>)}</ol>
                    <div className="code-evidence-grid">{['source', 'sink'].map((kind) => <div key={kind}><strong>{kind.toUpperCase()} · {item.file}</strong><pre dir="ltr"><code>{item.code_evidence?.[kind]?.length ? item.code_evidence[kind].map((row) => `${row.line}  ${row.text}${row.truncated ? ' …' : ''}`).join('\n') : 'Excerpt unavailable for this saved record.'}</code></pre></div>)}</div>
                    <button className="button button-secondary" onClick={() => navigate(`/projects/${encodeURIComponent(projectId)}/findings/${encodeURIComponent(item.id)}?${new URLSearchParams({ file: item.file })}`)} type="button">{ar ? 'افتح الدليل والإصلاح المقترح' : 'Open evidence and proposed repair'}</button>
                  </article>
                )) : <p className="analysis-empty">{ar ? 'لا توجد مرشحات مبنية على أدلة ضمن النطاق المدعوم.' : 'No evidence-backed candidates within the supported scope.'}</p>}
                <h3>{ar ? 'مسارات لم تُرقَّ إلى نتيجة' : 'Paths not promoted to findings'}</h3>
                {report.technical.non_candidate_paths.length ? report.technical.non_candidate_paths.map((item, index) => (
                  <p key={`${item.file}:${item.sink?.start_line}:${index}`}>
                    <code dir="ltr">{item.file} · {item.assessment?.pack} · {item.assessment?.status} · {item.assessment?.basis}</code>
                  </p>
                )) : <p className="analysis-empty">{ar ? 'لا توجد مسارات مستبعدة أو غير محسومة.' : 'No excluded or unresolved paths.'}</p>}
                <p>{ar ? 'فحص OSV: ' : 'OSV lookup: '}{report.technical.dependency_advisories.status}</p>
                <h3>{ar ? 'توصيات' : 'Recommendations'}</h3>
                <ul>{report.technical.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
                <h3>{ar ? 'حدود تقنية' : 'Technical limitations'}</h3>
                <ul>{report.technical.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
              </section>
            ) : null}

            {section === 'closure' ? (
              <section className="report-document">
                <h2>{ar ? 'دليل الإغلاق' : 'Evidence of closure'}</h2>
                <StatusBadge tone="warning">{report.closure_evidence.status}</StatusBadge>
                <p>{ar ? 'لا يُسمح بقرار VERIFIED CLOSED قبل الاختبار الوظيفي، إعادة السيناريو، إعادة الفحص والتتبع، وحفظ الدليل.' : 'VERIFIED CLOSED requires functional testing, replay, re-scan, re-trace, and preserved evidence.'}</p>
                <p><code dir="ltr">FUNCTIONAL_TEST: {report.closure_evidence.functional_test} · REPLAY: {report.closure_evidence.replay} · RE_SCAN: {report.closure_evidence.re_scan} · RE_TRACE: {report.closure_evidence.re_trace}</code></p>
              </section>
            ) : null}

            <div className="progress-actions">
              <button className="button button-ghost" onClick={() => navigate(`/analysis/progress/${encodeURIComponent(projectId)}`)} type="button"><Icon name="arrow" />{ar ? 'العودة للتحليل' : 'Back to analysis'}</button>
            </div>
          </>
        ) : null}
      </section>
    </AppShell>
  );
}
