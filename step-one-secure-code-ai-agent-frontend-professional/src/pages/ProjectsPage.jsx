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
  const { data: projects, error, loading, reload } = useAsyncResource(getProjects, []);

  return (
    <AppShell>
      <section className="page-title-row">
        <div>
          <span className="eyebrow">{ar ? 'السجلات المحفوظة' : 'Saved records'}</span>
          <h1>{ar ? 'التحليلات' : 'Analyses'}</h1>
          <p>
            {ar
              ? 'افتح نتائج تحليل محفوظ أو ابدأ تحليل ملف أو مشروع جديد. تظهر أحدث 20 نتيجة تملكها.'
              : 'Open a saved analysis or start a new file or project analysis. Your latest 20 results appear here.'}
          </p>
        </div>
        <button className="button button-primary" onClick={() => navigate('/analysis/new')} type="button">
          <Icon name="scan" />
          {ar ? 'تحليل جديد' : 'New analysis'}
        </button>
      </section>

      <AsyncState
        empty={!loading && !error && projects?.length === 0}
        emptyLabel={ar ? 'لا توجد تحليلات محفوظة بعد.' : 'No saved analyses yet.'}
        error={error}
        loading={loading}
        loadingLabel={ar ? 'تحميل التحليلات…' : 'Loading analyses…'}
        onRetry={reload}
      />

      {!loading && !error && projects?.length ? (
        <section className="project-list">
          {projects.map((project) => (
            <article className="project-row" key={project.analysis_id}>
              <div className="project-icon">
                <Icon name="code" />
              </div>
              <div className="project-main">
                <div className="project-name-row">
                  <h2><bdi dir="ltr">{project.artifact_name}</bdi></h2>
                  <StatusBadge tone="info">
                    {ar ? 'تحليل ساكن' : 'Static analysis'}
                  </StatusBadge>
                </div>
                <p>
                  <bdi dir="ltr">{project.scope}</bdi> ·{' '}
                  <bdi dir="ltr">{project.language ?? project.project_type ?? 'Unknown'}</bdi>
                </p>
                <div className="project-meta">
                  <span className="technical-value">{project.integrity}</span>
                  <span className="technical-value">{project.analysis_id}</span>
                  <span>{new Date(project.created_at).toLocaleString(ar ? 'ar-JO' : 'en-US')}</span>
                </div>
              </div>
              <button
                className="button button-secondary"
                onClick={() => navigate(`/analysis/progress/${encodeURIComponent(project.analysis_id)}`)}
                type="button"
              >
                {ar ? 'فتح النتيجة' : 'Open result'}
                <Icon name="arrow" />
              </button>
            </article>
          ))}
        </section>
      ) : null}
    </AppShell>
  );
}
