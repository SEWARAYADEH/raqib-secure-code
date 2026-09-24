import { useLanguage } from '../i18n';
import StatusBadge from './StatusBadge';

export default function ProjectPassport({ project }) {
  const { language } = useLanguage();
  const ar = language === 'ar';

  const items = [
    [ar ? 'الإصدار' : 'Version', project.version],
    [ar ? 'الفرع' : 'Branch', project.branch],
    [ar ? 'معرّف التحليل' : 'Analysis ID', project.analysisId],
    [ar ? 'تاريخ الإنشاء' : 'Created', project.createdAt],
    [ar ? 'اللغة' : 'Language', project.language],
    [ar ? 'الإطار' : 'Framework', project.framework],
    [ar ? 'نمط الفحص' : 'Scan mode', project.scanMode],
    [ar ? 'التغطية' : 'Coverage', project.coverage],
    [ar ? 'دور الذكاء الاصطناعي' : 'AI role', project.aiUsage],
  ];

  return (
    <section className="passport-card">
      <div className="passport-heading">
        <div>
          <span className="eyebrow">{ar ? 'هوية التحليل' : 'Project passport'}</span>
          <h1>{project.name}</h1>
          <p>
            <bdi dir="ltr">{project.projectType}</bdi>
            {' · '}
            <bdi dir="ltr">{project.scannerPack}</bdi>
          </p>
        </div>
        <div className="passport-state">
          <StatusBadge tone="warning">
            {ar && project.evidenceState === 'Partial' ? 'أدلة جزئية' : project.evidenceState}
          </StatusBadge>
          <small className="technical-value">{project.lastScan}</small>
        </div>
      </div>

      <div className="passport-grid">
        {items.map(([label, value]) => (
          <div className="passport-item" key={label}>
            <span>{label}</span>
            <strong className="technical-value">{value}</strong>
          </div>
        ))}
      </div>

      <div className="passport-foot">
        <span className="technical-value">{project.standards}</span>
        <span className="technical-value" title={project.aiDefinition}>{project.aiEngine}</span>
      </div>
    </section>
  );
}
