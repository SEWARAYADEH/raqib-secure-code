import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import StatusBadge from '../components/StatusBadge';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

export default function ProjectsPage() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState('all');
  const { data: projects, error, loading, reload } = useAsyncResource(getProjects, []);
  const saved = projects ?? [];
  const visible = useMemo(() => saved.filter((project) => {
    const matchesScope = scope === 'all'
      || (scope === 'project' ? project.scope === 'PROJECT_STATIC_MODEL' : project.scope === 'FILE');
    const text = `${project.artifact_name} ${project.language ?? ''} ${project.project_type ?? ''}`.toLowerCase();
    return matchesScope && text.includes(query.trim().toLowerCase());
  }), [projects, query, scope]);
  const totals = {
    files: saved.reduce((sum, item) => sum + (item.files_analyzed ?? 0), 0),
    paths: saved.reduce((sum, item) => sum + (item.observed_paths ?? 0), 0),
    candidates: saved.reduce((sum, item) => sum + (item.candidate_count ?? 0), 0),
  };

  return (
    <AppShell>
      <section className="projects-dashboard">
        <header className="dashboard-intro">
          <div><span className="eyebrow">RAQEEB / WORKSPACE</span><h1>{ar ? 'لوحة العمل' : 'Workspace'}</h1><p>{ar ? 'تحليلاتك المحفوظة، من المشروع إلى الدليل.' : 'Your saved analyses, from project to evidence.'}</p></div>
          <button className="button button-primary" onClick={() => navigate('/analysis/new')} type="button"><Icon name="upload" />{ar ? 'تحليل جديد' : 'New analysis'}</button>
        </header>

        {!loading && !error && (
          <div className="dashboard-summary" aria-label={ar ? 'ملخص آخر التحليلات' : 'Recent analysis summary'}>
            <div><span>{ar ? 'التحليلات' : 'Analyses'}</span><strong>{saved.length}</strong></div>
            <div><span>{ar ? 'ملفات محللة' : 'Analyzed files'}</span><strong>{totals.files}</strong></div>
            <div><span>{ar ? 'مسارات مرصودة' : 'Observed paths'}</span><strong>{totals.paths}</strong></div>
            <div><span>{ar ? 'مرشحات أمنية' : 'Candidates'}</span><strong>{totals.candidates}</strong></div>
          </div>
        )}

        <div className="dashboard-section-head"><div><h2>{ar ? 'التحليلات المحفوظة' : 'Saved analyses'}</h2><p>{ar ? 'آخر 20 سجلًا تملكها؛ المرشح ليس ثغرة مثبتة.' : 'Your latest 20 records; a candidate is not a verified vulnerability.'}</p></div></div>

        <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل التحليلات…' : 'Loading analyses…'} onRetry={reload} />
        {!loading && !error && saved.length > 0 && (
          <>
            <div className="dashboard-filters">
              <label><Icon name="search" /><span className="sr-only">{ar ? 'بحث في التحليلات' : 'Search analyses'}</span><input onChange={(event) => setQuery(event.target.value)} placeholder={ar ? 'ابحث باسم المشروع أو اللغة' : 'Search artifact or language'} type="search" value={query} /></label>
              <div className="dashboard-scope" role="group" aria-label={ar ? 'نوع التحليل' : 'Analysis scope'}>
                {[['all', ar ? 'الكل' : 'All'], ['file', ar ? 'ملف' : 'File'], ['project', ar ? 'مشروع ZIP' : 'ZIP project']].map(([value, label]) => <button aria-pressed={scope === value} key={value} onClick={() => setScope(value)} type="button">{label}</button>)}
              </div>
            </div>
            {visible.length ? <div className="dashboard-records">{visible.map((project) => {
              const id = encodeURIComponent(project.analysis_id);
              return <article className="dashboard-record" key={project.analysis_id}>
                <div className="dashboard-record-main"><span className="record-type">{project.scope === 'PROJECT_STATIC_MODEL' ? 'ZIP / PROJECT' : 'CODE / FILE'}</span><h3 dir="auto">{project.artifact_name}</h3><p dir="ltr">{project.language ?? project.project_type ?? 'Unknown'} · {project.files_analyzed ?? '?'} {ar ? 'ملف' : 'files'} · {project.observed_paths ?? '?'} {ar ? 'مسار' : 'paths'}</p></div>
                <div className="dashboard-record-state"><StatusBadge tone={project.candidate_count ? 'warning' : 'neutral'}>{project.candidate_count ?? '?'} CANDIDATE</StatusBadge><small>{new Date(project.created_at).toLocaleDateString(ar ? 'ar-JO' : 'en-US')}</small></div>
                <div className="dashboard-record-actions"><button className="button button-secondary" onClick={() => navigate(`/analysis/progress/${id}`)} type="button">{ar ? 'النتيجة' : 'Result'}</button><button className="button button-ghost" onClick={() => navigate(`/projects/${id}/workbench`)} type="button">{ar ? 'البنية' : 'Structure'}</button></div>
              </article>;
            })}</div> : <div className="analysis-empty">{ar ? 'لا توجد تحليلات تطابق البحث أو النوع المحدد.' : 'No analyses match this search or scope.'}</div>}
          </>
        )}
        {!loading && !error && saved.length === 0 && <div className="dashboard-empty"><Icon name="code" size={32} /><h2>{ar ? 'ابدأ بأول تحليل' : 'Start your first analysis'}</h2><p>{ar ? 'ارفع ملف .py أو .js أو .jsx أو مشروع ZIP. ستظهر النتيجة هنا بعد حفظها.' : 'Upload a .py, .js, .jsx file or ZIP project. Its saved result appears here.'}</p><button className="button button-primary" onClick={() => navigate('/analysis/new')} type="button">{ar ? 'ارفع مشروعك' : 'Upload project'}</button></div>}
      </section>
    </AppShell>
  );
}
