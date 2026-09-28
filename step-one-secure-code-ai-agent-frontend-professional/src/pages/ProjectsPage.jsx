import { useNavigate } from 'react-router-dom';
import { getProjects } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import StatusBadge from '../components/StatusBadge';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

function formatDate(value, language) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat(language === 'ar' ? 'ar-JO' : 'en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function projectLabel(project, ar) {
  if (project.scope === 'PROJECT_STATIC_MODEL') {
    return project.project_type || (ar ? 'مشروع كود' : 'Code project');
  }
  return ar ? 'ملف كود' : 'Source file';
}

export default function ProjectsPage() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data: projects, error, loading, reload } = useAsyncResource(getProjects, []);

  return (
    <AppShell>
      <section className="page-title-row">
        <div>
          <span className="eyebrow">{ar ? 'سجل التحليلات الحقيقي' : 'Live analysis registry'}</span>
          <h1>{ar ? 'التحليلات المحفوظة' : 'Saved analyses'}</h1>
          <p>
            {ar
              ? 'هذه القائمة تأتي من التخزين الفعلي في الـBackend. كل سجل مرتبط بصاحبه ويتم التحقق من سلامته قبل عرضه.'
              : 'This list comes from backend persistence. Every record is owner-scoped and integrity-checked before it is shown.'}
          </p>
        </div>
        <button className="button button-primary" onClick={() => navigate('/analysis/new')} type="button">
          <Icon name="scan" />
          {ar ? 'تحليل جديد' : 'New analysis'}
        </button>
      </section>

      <AsyncState
        empty={!loading && !error && projects?.length === 0}
        emptyLabel={ar ? 'لا توجد تحليلات محفوظة بعد. ابدأ تحليلًا جديدًا.' : 'No saved analyses yet. Start a new analysis.'}
        error={error}
        loading={loading}
        loadingLabel={ar ? 'تحميل السجل المحمي…' : 'Loading protected registry…'}
        onRetry={reload}
      />

      {!loading && !error && projects?.length ? (
        <section className="project-list">
          {projects.map((project) => (
            <article className="project-row" key={project.analysis_id}>
              <div className="project-icon">
                <Icon name={project.scope === 'PROJECT_STATIC_MODEL' ? 'projects' : 'code'} />
              </div>

              <div className="project-main">
                <div className="project-name-row">
                  <h2><bdi dir="ltr">{project.artifact_name}</bdi></h2>
                  <StatusBadge tone="success">
                    {project.integrity === 'HMAC-SHA256'
                      ? (ar ? 'سلامة السجل متحققة' : 'Integrity verified')
                      : project.integrity}
                  </StatusBadge>
                </div>

                <p>
                  {projectLabel(project, ar)}
                  {project.language ? <> · <bdi dir="ltr">{project.language}</bdi></> : null}
                </p>

                <div className="project-meta">
                  <span className="technical-value">{project.analysis_id}</span>
                  <span>{formatDate(project.created_at, language)}</span>
                </div>
              </div>

              <button
                className="button button-secondary"
                onClick={() => navigate(`/analyses/${encodeURIComponent(project.analysis_id)}`)}
                type="button"
              >
                {ar ? 'فتح النتيجة الحقيقية' : 'Open live result'}
                <Icon name="arrow" />
              </button>
            </article>
          ))}
        </section>
      ) : null}
    </AppShell>
  );
}
