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
          <span className="eyebrow">{ar ? 'مساحات العمل' : 'Workspaces'}</span>
          <h1>{ar ? 'المشاريع' : 'Projects'}</h1>
          <p>
            {ar
              ? 'افتح مشروعًا موجودًا أو ابدأ تحليلًا جديدًا. كل مشروع يقود إلى Workbench واحدة واضحة.'
              : 'Open an existing project or prepare a new analysis. Every project leads to one focused workbench.'}
          </p>
        </div>
        <button className="button button-primary" onClick={() => navigate('/analysis/new')} type="button">
          <Icon name="scan" />
          {ar ? 'تحليل جديد' : 'New analysis'}
        </button>
      </section>

      <AsyncState
        empty={!loading && !error && projects?.length === 0}
        emptyLabel={ar ? 'لا توجد مشاريع بعد.' : 'No projects yet.'}
        error={error}
        loading={loading}
        loadingLabel={ar ? 'تحميل المشاريع…' : 'Loading projects…'}
        onRetry={reload}
      />

      {!loading && !error && projects?.length ? (
        <section className="project-list">
          {projects.map((project) => (
            <article className="project-row" key={project.id}>
              <div className="project-icon">
                <Icon name="code" />
              </div>
              <div className="project-main">
                <div className="project-name-row">
                  <h2>{project.name}</h2>
                  <StatusBadge tone={project.status === 'Verified' ? 'success' : 'info'}>
                    {ar
                      ? project.status === 'Verified'
                        ? 'تم التحقق'
                        : 'تحليل تجريبي جاهز'
                      : project.status}
                  </StatusBadge>
                  {project.demo ? (
                    <StatusBadge tone="neutral">{ar ? 'بيانات تجريبية' : 'Demo data'}</StatusBadge>
                  ) : null}
                </div>
                <p>
                  <bdi dir="ltr">{project.type}</bdi> · <bdi dir="ltr">{project.language}</bdi> ·{' '}
                  <bdi dir="ltr">{project.framework}</bdi>
                </p>
                <div className="project-meta">
                  <span className="technical-value">v{project.version}</span>
                  <span className="technical-value">{project.branch}</span>
                  <span>{ar ? `${project.findings} نتائج` : `${project.findings} findings`}</span>
                  <span className="technical-value">{project.lastScan}</span>
                </div>
              </div>
              <button
                className="button button-secondary"
                onClick={() => navigate(`/projects/${project.id}/workbench`)}
                type="button"
              >
                {ar ? 'فتح مساحة العمل' : 'Open workbench'}
                <Icon name="arrow" />
              </button>
            </article>
          ))}
        </section>
      ) : null}
    </AppShell>
  );
}
