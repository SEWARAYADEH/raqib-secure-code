import { useState } from 'react';
import { getReport, getWorkbench } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import ProjectPassport from '../components/ProjectPassport';
import StatusBadge from '../components/StatusBadge';
import UpdatedFileDownload from '../components/UpdatedFileDownload';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

function severityLabel(severity, ar) {
  if (!ar) return severity;
  if (severity === 'Critical') return 'حرجة';
  if (severity === 'High') return 'عالية';
  return 'متوسطة';
}

function verificationKeyLabel(key, ar) {
  if (!ar) return key;
  const labels = {
    functional: 'الاختبار الوظيفي',
    replay: 'إعادة الاختبار',
    rescan: 'إعادة الفحص',
    retrace: 'إعادة التتبع',
    closure: 'حالة المعالجة',
  };
  return labels[key] ?? key;
}

function verificationValueLabel(value, ar) {
  if (!ar) return value;
  const labels = {
    Pass: 'ناجح',
    Pending: 'بانتظار التحقق',
    'Candidate fix': 'إصلاح مرشح',
    'Verified remediated': 'تم التحقق من المعالجة',
    'Not applicable': 'غير منطبق',
    'Pending environment validation': 'بانتظار التحقق من بيئة التشغيل',
    'Previous cross-account request is denied': 'تم رفض طلب الوصول السابق بين حسابين',
    'Original finding not reproduced': 'لم تعد النتيجة الأصلية قابلة لإعادة الإنتاج',
    'Ownership control appears before resource return': 'ظهر فحص الملكية قبل إرجاع المورد',
  };
  return labels[value] ?? value;
}

const technologyLabels = {
  language: 'اللغة',
  framework: 'الإطار',
  architecture: 'البنية',
  database: 'قاعدة البيانات',
  dependencies: 'الاعتماديات',
};

const aiLabels = {
  'Code explanation': 'شرح الكود',
  'Finding detection': 'اكتشاف النتائج',
  'Finding correlation': 'ربط النتائج بالسياق',
  'Fix proposal': 'اقتراح الإصلاح',
  Verification: 'التحقق',
  'Closure decision': 'قرار الإغلاق',
  'AI assisted': 'بمساعدة الذكاء الاصطناعي',
  'Deterministic scanner': 'Scanner حتمي',
  'Deterministic evidence': 'أدلة تحقق حتمية',
  'Evidence based': 'مبني على الأدلة',
};

export default function ReportPage() {
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [mode, setMode] = useState('executive');
  const reportState = useAsyncResource(getReport, []);
  const workbenchState = useAsyncResource(getWorkbench, []);
  const loading = reportState.loading || workbenchState.loading;
  const error = reportState.error || workbenchState.error;
  const report = reportState.data;
  const passport = workbenchState.data?.passport;

  const retry = () => {
    reportState.reload();
    workbenchState.reload();
  };

  return (
    <AppShell>
      <AsyncState
        error={error}
        loading={loading}
        loadingLabel={ar ? 'تجهيز التقرير…' : 'Preparing report…'}
        onRetry={retry}
      />

      {!loading && !error && report && passport ? (
        <>
          <ProjectPassport project={passport} />

          <section className="report-toolbar">
            <div className="segmented-control">
              <button
                className={mode === 'executive' ? 'active' : ''}
                onClick={() => setMode('executive')}
                type="button"
              >
                {ar ? 'ملخص تنفيذي' : 'Executive report'}
              </button>
              <button
                className={mode === 'engineering' ? 'active' : ''}
                onClick={() => setMode('engineering')}
                type="button"
              >
                {ar ? 'تقرير هندسي' : 'Engineering report'}
              </button>
            </div>
            <button className="button button-secondary" onClick={() => window.print()} type="button">
              <Icon name="report" />
              {ar ? 'طباعة / حفظ PDF' : 'Print / Save PDF'}
            </button>
          </section>

          {mode === 'executive' ? (
            <article className="report-document">
              <header className="report-cover">
                <div>
                  <span className="eyebrow">SECCLOSURE · RAQEEB · FRONTEND DEMO DATA</span>
                  <h1>{ar ? 'تقرير الحالة الأمنية' : 'Security posture report'}</h1>
                  <p className="technical-value">{passport.name} · {passport.analysisId}</p>
                </div>
                <StatusBadge tone="warning">
                  {ar ? 'المخاطر المتبقية' : 'Residual risk'} ·{' '}
                  {ar && report.executive.residualRisk === 'Medium'
                    ? 'متوسطة'
                    : report.executive.residualRisk}
                </StatusBadge>
              </header>

              <section className="report-metrics">
                <div>
                  <span>{ar ? 'النتائج عند البداية' : 'Initial findings'}</span>
                  <strong>{report.executive.initialFindings}</strong>
                </div>
                <div>
                  <span>{ar ? 'النتائج الحالية' : 'Current findings'}</span>
                  <strong>{report.executive.currentFindings}</strong>
                </div>
                <div>
                  <span>{ar ? 'معالجات تم التحقق منها' : 'Verified remediated'}</span>
                  <strong>{report.executive.verifiedRemediated}</strong>
                </div>
                <div>
                  <span>{ar ? 'تغطية الفحص' : 'Scan coverage'}</span>
                  <strong>{report.executive.coverage}</strong>
                </div>
                <div>
                  <span>{ar ? 'تغطية الأدلة' : 'Evidence coverage'}</span>
                  <strong>{report.executive.evidenceCoverage}</strong>
                </div>
              </section>

              <section className="report-section">
                <div className="report-section-title">
                  <span>01</span>
                  <h2>{ar ? 'ملخص التحسن' : 'Improvement summary'}</h2>
                </div>
                <div className="before-after-grid">
                  <div>
                    <span>{ar ? 'قبل' : 'BEFORE'}</span>
                    <strong>
                      {report.executive.initialFindings} {ar ? 'نتائج' : 'findings'}
                    </strong>
                    <p>
                      {report.executive.criticalBefore} {ar ? 'نتيجة حرجة' : 'critical finding'}
                    </p>
                  </div>
                  <Icon name="arrow" size={28} />
                  <div>
                    <span>{ar ? 'بعد' : 'AFTER'}</span>
                    <strong>
                      {report.executive.currentFindings} {ar ? 'نتائج' : 'findings'}
                    </strong>
                    <p>
                      {report.executive.criticalAfter} {ar ? 'نتائج حرجة' : 'critical findings'}
                    </p>
                  </div>
                </div>
              </section>

              <section className="report-section">
                <div className="report-section-title">
                  <span>02</span>
                  <h2>{ar ? 'الملف التقني' : 'Technology profile'}</h2>
                </div>
                <div className="report-table">
                  {Object.entries(report.technology).map(([key, value]) => (
                    <div key={key}>
                      <span>{ar ? technologyLabels[key] ?? key : key}</span>
                      <strong className="technical-value">{value}</strong>
                    </div>
                  ))}
                </div>
              </section>

              <section className="report-section">
                <div className="report-section-title">
                  <span>03</span>
                  <h2>{ar ? 'دور الذكاء الاصطناعي' : 'AI involvement'}</h2>
                </div>
                <p className="report-lead">
                  {ar
                    ? 'يساعد الذكاء الاصطناعي في الفهم والربط واقتراح الإصلاح. قرار الإغلاق يعتمد على أدلة قابلة للمراجعة.'
                    : 'AI assists understanding, correlation, and candidate generation. Closure depends on reviewable evidence.'}
                </p>
                <div className="report-table">
                  {report.aiMatrix.map(([stage, source]) => (
                    <div key={stage}>
                      <span>{ar ? aiLabels[stage] ?? stage : stage}</span>
                      <strong>{ar ? aiLabels[source] ?? source : source}</strong>
                    </div>
                  ))}
                </div>
              </section>

              <section className="report-section">
                <div className="report-section-title">
                  <span>04</span>
                  <h2>{ar ? 'المعايير المستخدمة' : 'Standards used'}</h2>
                </div>
                <div className="role-pills report-standards technical-pills">
                  {report.standards.map((item) => <span key={item}>{item}</span>)}
                </div>
              </section>
            </article>
          ) : (
            <article className="report-document engineering-report">
              <header className="report-cover">
                <div>
                  <span className="eyebrow">ENGINEERING EVIDENCE · FRONTEND DEMO DATA</span>
                  <h1>{ar ? 'تفاصيل النتائج والإصلاحات' : 'Findings and remediation evidence'}</h1>
                  <p className="technical-value">{passport.analysisId} · {passport.standards}</p>
                </div>
              </header>

              {report.findings.map((finding, index) => (
                <section className="engineering-finding" key={finding.id}>
                  <div className="engineering-finding-head">
                    <div>
                      <span className="eyebrow technical-value">
                        {String(index + 1).padStart(2, '0')} · {finding.id}
                      </span>
                      <h2>{ar ? finding.titleAr ?? finding.title : finding.title}</h2>
                    </div>
                    <StatusBadge tone={finding.severity === 'Critical' ? 'danger' : 'warning'}>
                      {severityLabel(finding.severity, ar)}
                    </StatusBadge>
                  </div>

                  <div className="report-table compact-table">
                    <div>
                      <span>CWE</span>
                      <strong className="technical-value">{finding.cwe}</strong>
                    </div>
                    <div>
                      <span>{ar ? 'الدالة' : 'Function'}</span>
                      <strong className="technical-value">
                        {finding.function ?? (ar ? 'إعدادات' : 'Configuration')}
                      </strong>
                    </div>
                    <div><span>{ar ? 'السطر' : 'Line'}</span><strong>{finding.line}</strong></div>
                    <div>
                      <span>{ar ? 'المعيار' : 'Standard'}</span>
                      <strong className="technical-value technical-wrap">{finding.standard}</strong>
                    </div>
                    <div>
                      <span>{ar ? 'السبب الجذري' : 'Root cause'}</span>
                      <strong>{ar ? finding.rootCauseAr ?? finding.rootCause : finding.rootCause}</strong>
                    </div>
                    <div>
                      <span>{ar ? 'الدليل' : 'Evidence'}</span>
                      <strong>{ar ? finding.evidenceAr ?? finding.evidence : finding.evidence}</strong>
                    </div>
                  </div>

                  <div className="report-code-compare" dir="ltr">
                    <div>
                      <span>WEAK CODE</span>
                      <pre>{finding.weakCode}</pre>
                    </div>
                    <div>
                      <span>SECURE CANDIDATE</span>
                      <pre>{finding.secureCode}</pre>
                    </div>
                  </div>

                  <div className="verification-list report-verification">
                    {Object.entries(finding.verification).map(([key, value]) => (
                      <div className="verification-row" key={key}>
                        <span>{verificationKeyLabel(key, ar)}</span>
                        <strong>{verificationValueLabel(value, ar)}</strong>
                      </div>
                    ))}
                  </div>

                  <UpdatedFileDownload ar={ar} finding={finding} />
                </section>
              ))}
            </article>
          )}
        </>
      ) : null}
    </AppShell>
  );
}
