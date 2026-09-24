import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';
import StatusBadge from '../components/StatusBadge';
import { useLanguage } from '../i18n';

function summarizeFile(result, ar) {
  const structure = result.structure?.counts ?? {};
  const semantics = result.security_semantics?.counts ?? {};
  const localPaths = result.data_flow?.counts?.observed_paths ?? 0;
  const crossFunctionPaths = result.inter_function_data_flow?.counts?.observed_paths ?? 0;
  const understanding = result.application_understanding ?? {};
  const findings = result.security_analysis?.candidates ?? [];
  const verificationPlans = result.exploitability_verification?.plans ?? [];
  return {
    name: result.artifact?.relative_path ?? result.artifact?.filename ?? 'source',
    language: result.language?.candidate ?? result.structure?.language ?? 'Unknown',
    syntaxValid: result.structure?.syntax?.valid === true,
    metrics: [
      [ar ? 'الدوال' : 'Functions', structure.functions ?? 0],
      [ar ? 'الاستدعاءات' : 'Calls', structure.calls ?? 0],
      [ar ? 'الإسنادات' : 'Assignments', structure.assignments ?? 0],
      [ar ? 'المصادر' : 'Sources', semantics.sources ?? 0],
      [ar ? 'المصارف' : 'Sinks', semantics.sinks ?? 0],
      [ar ? 'مسارات داخلية' : 'Local paths', localPaths],
      [ar ? 'مسارات بين الدوال' : 'Cross-function paths', crossFunctionPaths],
      [ar ? 'المسارات HTTP' : 'HTTP routes', understanding.counts?.routes ?? 0],
      [ar ? 'الخدمات' : 'Services', understanding.counts?.services ?? 0],
      [ar ? 'عمليات قاعدة البيانات' : 'Database operations', understanding.counts?.database_operations ?? 0],
    ],
    role: understanding.project_role ?? 'UNKNOWN_COMPONENT',
    frameworks: understanding.frameworks ?? [],
    findings,
    verificationPlans,
    paths: [...(result.data_flow?.paths ?? []), ...(result.inter_function_data_flow?.paths ?? [])],
  };
}

function AnalysisFileCard({ file, ar }) {
  return (
    <article className="analysis-result-card">
      <div className="analysis-result-head">
        <div><span className="eyebrow">{file.language}</span><h2><bdi dir="ltr">{file.name}</bdi></h2></div>
        <StatusBadge tone={file.syntaxValid ? 'success' : 'danger'}>
          {file.syntaxValid ? (ar ? 'Syntax صالح' : 'Valid syntax') : (ar ? 'Syntax غير صالح' : 'Invalid syntax')}
        </StatusBadge>
      </div>
      <div className="analysis-metrics">
        {file.metrics.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
      </div>
      <div className="analysis-paths">
        <h3>{ar ? 'فهم التطبيق' : 'Application understanding'}</h3>
        <p><strong>{file.role}</strong>{file.frameworks.length
          ? ` · ${file.frameworks.map((item) => `${item.name} (${item.status})`).join(', ')}`
          : ` · ${ar ? 'Framework غير مثبت' : 'No framework established'}`}</p>
      </div>
      <div className="analysis-paths">
        <h3>{ar ? 'مسارات الأدلة المرصودة' : 'Observed evidence paths'}</h3>
        {file.paths.length ? file.paths.map((path, index) => (
          <div className="analysis-path" key={`${path.kind}-${index}`}>
            <div className="analysis-path-title"><StatusBadge tone="warning">OBSERVED</StatusBadge><strong>{path.kind}</strong><span>{path.evidence_strength}</span></div>
            <ol>{path.trace.map((step, stepIndex) => (
              <li key={`${step.kind}-${step.line ?? stepIndex}-${stepIndex}`}>
                <span>{step.kind}</span>
                <code dir="ltr">{step.target ?? step.value ?? step.name ?? `${step.caller} → ${step.callee}`}</code>
                {step.line ? <small>line {step.line}</small> : null}
              </li>
            ))}</ol>
            <p>{path.controls_observed?.length
              ? (ar ? 'تم رصد عناصر تحكم أمنية، لكن ملاءمتها غير مثبتة بعد.' : 'Security controls were observed, but their applicability is not yet proven.')
              : (ar ? 'لم يُرصد عنصر تحكم على هذا المسار. هذا ليس إثبات ثغرة.' : 'No control was observed on this path. This is not proof of a vulnerability.')}</p>
          </div>
        )) : <p className="analysis-empty">{ar ? 'لم يثبت المحرك مسارًا من مصدر إلى مصرف حساس ضمن النطاق المدعوم.' : 'The engine did not establish a source-to-sensitive-sink path within the supported scope.'}</p>}
      </div>
      <div className="analysis-paths">
        <h3>{ar ? 'مرشحات النتائج والتحقق' : 'Finding candidates and verification'}</h3>
        {file.findings.length ? file.findings.map((finding) => {
          const plan = file.verificationPlans.find((item) => item.finding_id === finding.id);
          return (
            <div className="analysis-path" key={finding.id}>
              <div className="analysis-path-title">
                <StatusBadge tone="warning">{finding.state}</StatusBadge>
                <strong>{finding.title}</strong>
                <span>{finding.standards.status}</span>
              </div>
              <p>{ar
                ? `الوصول الساكن: ${finding.reachability.static_path} · قابلية الاستغلال: ${finding.exploitability.status}`
                : `Static reachability: ${finding.reachability.static_path} · Exploitability: ${finding.exploitability.status}`}</p>
              <p>{ar
                ? `التحقق: ${plan?.execution_status ?? 'NOT_RUN'} · العائق: ${plan?.blockers?.join(', ') || 'NONE'}`
                : `Verification: ${plan?.execution_status ?? 'NOT_RUN'} · Blocker: ${plan?.blockers?.join(', ') || 'NONE'}`}</p>
            </div>
          );
        }) : <p className="analysis-empty">{ar ? 'لا توجد مرشحات نتائج مبنية على مسار مثبت.' : 'No finding candidates were produced from an established path.'}</p>}
      </div>
    </article>
  );
}

export default function AnalysisProgressPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const payload = location.state?.analysis;
  if (!payload?.result) return <Navigate replace to="/analysis/new" />;

  const files = (payload.result.files ?? [payload.result]).map((item) => summarizeFile(item, ar));
  const totalPaths = files.reduce((sum, file) => sum + file.paths.length, 0);
  const persisted = payload.record?.persisted === true;

  return (
    <AppShell>
      <section className="progress-page analysis-results-page">
        <div className="page-title-row compact">
          <div><span className="eyebrow">{ar ? 'نتيجة المحرك الحقيقي' : 'Live engine result'}</span><h1>{ar ? 'اكتمل التحليل الساكن' : 'Static analysis complete'}</h1><p>{ar ? 'النتائج أدلة هندسية مرصودة. لا يعتبر النظام أي مسار ثغرة أو إثبات استغلال في هذه المرحلة.' : 'Results are observed engineering evidence. No path is treated as a vulnerability or exploit proof at this stage.'}</p></div>
          <StatusBadge tone={totalPaths ? 'warning' : 'success'}>{totalPaths} {ar ? 'مسار مرصود' : 'observed paths'}</StatusBadge>
        </div>
        <div className="analysis-proof-strip">
          <div><span>{ar ? 'معرّف التحليل' : 'Analysis ID'}</span><strong className="technical-value">{payload.record?.analysis_id}</strong></div>
          <div><span>{ar ? 'سياسة التنفيذ' : 'Execution policy'}</span><strong>NEVER_EXECUTE_SOURCE</strong></div>
          <div><span>{ar ? 'سياسة النتائج' : 'Finding policy'}</span><strong>EVIDENCE_GATED_CANDIDATES</strong></div>
          <div><span>{ar ? 'الحفظ' : 'Persistence'}</span><strong>{persisted ? 'HMAC-SHA256' : (ar ? 'غير مفعّل محليًا' : 'Local persistence disabled')}</strong></div>
        </div>
        <div className="analysis-result-list">{files.map((file) => <AnalysisFileCard ar={ar} file={file} key={file.name} />)}</div>
        <div className="progress-actions">
          <button className="button button-ghost" onClick={() => navigate('/analysis/new')} type="button"><Icon name="scan" />{ar ? 'تحليل جديد' : 'New analysis'}</button>
          <button className="button button-primary" onClick={() => navigate('/projects')} type="button">{ar ? 'العودة للمشاريع' : 'Back to projects'}<Icon name="arrow" /></button>
        </div>
      </section>
    </AppShell>
  );
}
