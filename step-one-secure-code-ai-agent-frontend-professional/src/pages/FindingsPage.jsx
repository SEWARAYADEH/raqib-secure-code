import { useNavigate, useParams } from 'react-router-dom';
import { getStoredAnalysis } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

export default function FindingsPage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data, error, loading, reload } = useAsyncResource(() => getStoredAnalysis(projectId), [projectId]);
  const result = data?.record?.result;
  const findings = (result?.files ?? (result ? [result] : [])).flatMap((file) =>
    (file.security_analysis?.candidates ?? []).map((finding) => ({
      finding, path: file.artifact?.relative_path ?? file.artifact?.filename ?? 'Unknown',
    }))
  ).concat((result?.files ? result.security_analysis?.candidates ?? [] : []).map((finding) => ({
    finding,
    path: `${finding.cross_file?.source_file ?? 'Unknown'} → ${finding.cross_file?.target_file ?? 'Unknown'}`,
    selector: '@project',
  })));

  return <AppShell><section className="evidence-page">
    <header className="evidence-header"><button className="text-link" onClick={() => navigate(`/analysis/progress/${projectId}`)} type="button">← {ar ? 'ملخص التحليل' : 'Analysis summary'}</button><h1>{ar ? 'المشاكل المكتشفة' : 'Detected problems'}</h1><p>{ar ? 'مرشحات مدعومة بمسار ساكن؛ لا تعني ثغرات مثبتة.' : 'Static-path candidates; not verified vulnerabilities.'}</p></header>
    <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل النتائج المحفوظة…' : 'Loading saved findings…'} onRetry={reload} />
    {!loading && !error && !findings.length && <div className="analysis-empty">{ar ? 'لا توجد مرشحات ضمن النطاق المدعوم. هذا لا يثبت أن المشروع آمن.' : 'No candidates in supported coverage. This does not prove safety.'}</div>}
    <div className="result-finding-list">{findings.map(({ finding, path, selector }) => <article key={`${path}:${finding.id}`}><div><strong>{finding.pack_assessment?.pack?.replaceAll('_', ' ') ?? finding.sink?.category ?? 'Security candidate'}</strong><small dir="ltr">{path} · {finding.scope?.function ?? 'Unresolved'}() · Line {finding.sink?.start_line ?? '?'}</small></div><span className="candidate-state">CANDIDATE</span><button className="button button-ghost compact-button" onClick={() => navigate(`/projects/${encodeURIComponent(projectId)}/findings/${encodeURIComponent(finding.id)}?${new URLSearchParams({ file: selector ?? path })}`)} type="button">{ar ? 'افتح الدليل' : 'Inspect evidence'}</button></article>)}</div>
  </section></AppShell>;
}
