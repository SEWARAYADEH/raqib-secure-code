import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getWorkbench } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import StatusBadge from '../components/StatusBadge';
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

function findingStatus(finding) {
  return finding.verification?.closure === 'Verified remediated' ? 'Remediated' : 'Open';
}

export default function FindingsPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data, error, loading, reload } = useAsyncResource(getWorkbench, []);
  const [query, setQuery] = useState('');
  const [severity, setSeverity] = useState('all');
  const [status, setStatus] = useState('all');

  const findings = useMemo(() => {
    if (!data?.findings) return [];
    const normalized = query.trim().toLowerCase();

    return data.findings.filter((finding) => {
      const file = data.files.find((item) => item.id === finding.fileId);
      const haystack = [finding.id, finding.title, finding.titleAr, finding.cwe, file?.path]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      const matchesQuery = !normalized || haystack.includes(normalized);
      const matchesSeverity = severity === 'all' || finding.severity === severity;
      const matchesStatus = status === 'all' || findingStatus(finding) === status;
      return matchesQuery && matchesSeverity && matchesStatus;
    });
  }, [data, query, severity, status]);

  return (
    <AppShell>
      <section className="page-title-row">
        <div>
          <span className="eyebrow">SECURITY FINDINGS</span>
          <h1>{ar ? 'النتائج الأمنية' : 'Security findings'}</h1>
          <p>
            {ar
              ? 'رتّب النتائج حسب الأهمية، ثم افتح كل Finding بجانب دليلها والكود المرتبط بها.'
              : 'Prioritize findings, then inspect each one with its evidence and relevant code context.'}
          </p>
        </div>
        <button className="button button-secondary" onClick={() => navigate(`/projects/${projectId}/workbench`)} type="button">
          {ar ? 'فتح مساحة العمل' : 'Open workbench'}
        </button>
      </section>

      <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل النتائج…' : 'Loading findings…'} onRetry={reload} />

      {!loading && !error && data ? (
        <>
          <section className="finding-filters" aria-label={ar ? 'فلاتر النتائج' : 'Finding filters'}>
            <label>
              <span>{ar ? 'بحث' : 'Search'}</span>
              <input
                onChange={(event) => setQuery(event.target.value)}
                placeholder={ar ? 'العنوان، الملف، CWE…' : 'Title, file, CWE…'}
                type="search"
                value={query}
              />
            </label>
            <label>
              <span>{ar ? 'الشدة' : 'Severity'}</span>
              <select onChange={(event) => setSeverity(event.target.value)} value={severity}>
                <option value="all">{ar ? 'الكل' : 'All'}</option>
                <option value="Critical">{ar ? 'حرجة' : 'Critical'}</option>
                <option value="High">{ar ? 'عالية' : 'High'}</option>
                <option value="Medium">{ar ? 'متوسطة' : 'Medium'}</option>
              </select>
            </label>
            <label>
              <span>{ar ? 'الحالة' : 'Status'}</span>
              <select onChange={(event) => setStatus(event.target.value)} value={status}>
                <option value="all">{ar ? 'الكل' : 'All'}</option>
                <option value="Open">{ar ? 'مفتوحة' : 'Open'}</option>
                <option value="Remediated">{ar ? 'تمت معالجتها' : 'Remediated'}</option>
              </select>
            </label>
          </section>

          {findings.length ? (
            <section className="findings-table" aria-label={ar ? 'قائمة النتائج الأمنية' : 'Security findings list'}>
              <div className="findings-head" aria-hidden="true">
                <span>{ar ? 'النتيجة' : 'Finding'}</span>
                <span>{ar ? 'الموقع' : 'Location'}</span>
                <span>{ar ? 'المرجع' : 'Reference'}</span>
                <span>{ar ? 'الحالة' : 'Status'}</span>
                <span />
              </div>
              {findings.map((finding) => {
                const file = data.files.find((item) => item.id === finding.fileId);
                const currentStatus = findingStatus(finding);
                return (
                  <article className="finding-row" key={finding.id}>
                    <div className="finding-primary">
                      <div className="finding-row-topline">
                        <span className="technical-value">{finding.id}</span>
                        <StatusBadge tone={severityTone(finding.severity)}>{severityLabel(finding.severity, ar)}</StatusBadge>
                      </div>
                      <strong>{ar ? finding.titleAr ?? finding.title : finding.title}</strong>
                      <p>{ar ? finding.rootCauseAr ?? finding.rootCause : finding.rootCause}</p>
                    </div>
                    <div className="finding-location technical-block">
                      <strong>{file?.path ?? '—'}</strong>
                      <small>{ar ? `السطر ${finding.line}` : `line ${finding.line}`}</small>
                    </div>
                    <div className="finding-reference technical-block">
                      <strong>{finding.cwe}</strong>
                      <small>{finding.standard}</small>
                    </div>
                    <div>
                      <StatusBadge tone={currentStatus === 'Remediated' ? 'success' : 'neutral'}>
                        {ar
                          ? currentStatus === 'Remediated' ? 'تمت المعالجة' : 'مفتوحة'
                          : currentStatus}
                      </StatusBadge>
                    </div>
                    <button className="button button-ghost compact-button" onClick={() => navigate(`/projects/${projectId}/findings/${finding.id}`)} type="button">
                      {ar ? 'التفاصيل' : 'Inspect'}
                    </button>
                  </article>
                );
              })}
            </section>
          ) : (
            <section className="empty-panel">
              <strong>{ar ? 'لا توجد نتائج تطابق الفلاتر.' : 'No findings match these filters.'}</strong>
              <p>{ar ? 'غيّر البحث أو الفلاتر لعرض نتائج أخرى.' : 'Adjust search or filters to view other findings.'}</p>
              <button className="button button-secondary" onClick={() => { setQuery(''); setSeverity('all'); setStatus('all'); }} type="button">
                {ar ? 'إعادة ضبط الفلاتر' : 'Reset filters'}
              </button>
            </section>
          )}
        </>
      ) : null}
    </AppShell>
  );
}
