import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getStoredAnalysis } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AnimatedCount from '../components/AnimatedCount';
import AsyncState from '../components/AsyncState';
import StatusBadge from '../components/StatusBadge';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

function filePath(file) {
  return file.artifact?.relative_path ?? file.artifact?.filename ?? 'Unknown';
}

function fileCandidates(file) {
  return file.security_analysis?.candidates ?? [];
}

function EvidenceList({ title, items, render, empty }) {
  return (
    <section className="workspace-evidence-list">
      <h3>{title} <span>{items.length}</span></h3>
      {items.length ? (
        <ul>{items.map((item, index) => <li key={`${title}-${index}`}>{render(item)}</li>)}</ul>
      ) : <p>{empty}</p>}
    </section>
  );
}

export default function WorkbenchPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [selectedPath, setSelectedPath] = useState(null);
  const { data, error, loading, reload } = useAsyncResource(
    () => getStoredAnalysis(projectId), [projectId],
  );
  const result = data?.record?.result;
  const files = result?.files ?? (result ? [result] : []);
  const file = files.find((item) => filePath(item) === selectedPath) ?? files[0];
  const candidates = file ? fileCandidates(file) : [];
  const projectCandidates = result?.files ? result.security_analysis?.candidates ?? [] : [];
  const structure = file?.structure ?? {};
  const understanding = file?.application_understanding ?? {};
  const paths = [
    ...(file?.data_flow?.paths ?? []),
    ...(file?.inter_function_data_flow?.paths ?? []),
  ];

  return (
    <AppShell>
      <section className="workspace-page">
        <header className="page-title-row">
          <div>
            <span className="eyebrow">{ar ? 'مساحة أدلة حقيقية' : 'Saved evidence workspace'}</span>
            <h1>{ar ? 'بنية المشروع' : 'Project structure'}</h1>
            <p>{ar
              ? 'استكشف الملفات والدوال والمسارات والمرشحات من التحليل المحفوظ. لا يُحفظ الكود الخام في السجل.'
              : 'Explore files, functions, paths, and candidates from the saved analysis. Raw source is not retained.'}</p>
          </div>
          <button className="button button-secondary" onClick={() => navigate(`/analysis/progress/${encodeURIComponent(projectId)}`)} type="button">
            {ar ? 'ملخص التحليل' : 'Analysis summary'}
          </button>
        </header>
        <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل أدلة المشروع…' : 'Loading project evidence…'} onRetry={reload} />
        {!loading && !error && result && !files.length && (
          <div className="analysis-empty">{ar ? 'لا توجد ملفات محللة في هذا السجل.' : 'No analyzed files in this record.'}</div>
        )}
        {!loading && !error && file && (
          <>
            <div className="workspace-summary" aria-label={ar ? 'ملخص المشروع' : 'Project summary'}>
              <div><span>{ar ? 'الأصل' : 'Artifact'}</span><strong dir="auto">{result.artifact?.filename ?? 'Unknown'}</strong></div>
              <div><span>{ar ? 'الملفات' : 'Files'}</span><strong><AnimatedCount value={files.length} /></strong></div>
              <div><span>{ar ? 'مرشحات أمنية' : 'Candidates'}</span><strong><AnimatedCount value={files.reduce((sum, item) => sum + fileCandidates(item).length, 0) + projectCandidates.length} /></strong></div>
              <div><span>{ar ? 'سلامة السجل' : 'Record integrity'}</span><strong>{data.record.integrity}</strong></div>
            </div>
            <div className="workspace-layout">
              <aside className="workspace-files" aria-label={ar ? 'ملفات المشروع' : 'Project files'}>
                <h2>{ar ? 'الملفات المحللة' : 'Analyzed files'}</h2>
                {files.map((item) => (
                  <button
                    aria-current={item === file ? 'true' : undefined}
                    className={item === file ? 'active' : ''}
                    key={filePath(item)}
                    onClick={() => setSelectedPath(filePath(item))}
                    type="button"
                  >
                    <span dir="ltr">{filePath(item)}</span>
                    <small>{item.language?.candidate ?? 'Unknown'} · {fileCandidates(item).length} {ar ? 'مرشح' : 'candidates'}</small>
                  </button>
                ))}
              </aside>
              <div className="workspace-inspector" key={filePath(file)}>
                <div className="workspace-file-header">
                  <div><span className="eyebrow">{file.language?.candidate ?? 'Unknown language'}</span><h2 dir="auto">{filePath(file)}</h2></div>
                  <StatusBadge tone={candidates.length ? 'warning' : 'neutral'}>{candidates.length} CANDIDATE</StatusBadge>
                </div>
                <div className="workspace-file-facts">
                  <span>{ar ? 'الدوال' : 'Functions'} <strong>{structure.counts?.functions ?? 0}</strong></span>
                  <span>{ar ? 'الاستدعاءات' : 'Calls'} <strong>{structure.counts?.calls ?? 0}</strong></span>
                  <span>{ar ? 'المسارات' : 'Routes'} <strong>{understanding.counts?.routes ?? 0}</strong></span>
                  <span>{ar ? 'مسارات البيانات' : 'Data paths'} <strong>{paths.length}</strong></span>
                </div>
                <div className="workspace-evidence-grid">
                  <EvidenceList title={ar ? 'الدوال' : 'Functions'} items={structure.functions ?? []} empty={ar ? 'لا توجد دوال مستخرجة.' : 'No functions extracted.'} render={(item) => <><code dir="ltr">{item.name}</code><small>Line {item.start_line ?? '?'}</small></>} />
                  <EvidenceList title={ar ? 'الاستيرادات' : 'Imports'} items={structure.imports ?? []} empty={ar ? 'لا توجد استيرادات مستخرجة.' : 'No imports extracted.'} render={(item) => <code dir="ltr">{item.statement ?? item.module ?? 'Unresolved'}</code>} />
                  <EvidenceList title={ar ? 'مسارات HTTP' : 'HTTP routes'} items={understanding.routes ?? []} empty={ar ? 'لم يُثبت مسار HTTP.' : 'No HTTP route established.'} render={(item) => <code dir="ltr">{item.method ?? (Array.isArray(item.methods) ? item.methods.join(', ') : 'HTTP')} {item.path ?? item.route ?? 'Unresolved'}</code>} />
                  <EvidenceList title={ar ? 'مسارات البيانات المرصودة' : 'Observed data paths'} items={paths} empty={ar ? 'لا يوجد مسار مصدر إلى عملية حساسة ضمن النطاق المدعوم.' : 'No source-to-sensitive-operation path in supported coverage.'} render={(item) => <><code dir="ltr">{item.kind ?? 'OBSERVED_PATH'}</code><small>{item.evidence_strength ?? 'Unresolved strength'}</small></>} />
                </div>
                <section className="workspace-candidates">
                  <h3>{ar ? 'النتائج المرشحة' : 'Finding candidates'}</h3>
                  {candidates.length ? candidates.map((finding) => (
                    <button key={finding.id} onClick={() => navigate(`/projects/${encodeURIComponent(projectId)}/findings/${encodeURIComponent(finding.id)}?${new URLSearchParams({ file: filePath(file) })}`)} type="button">
                      <span><strong>{finding.pack_assessment?.pack?.replaceAll('_', ' ') ?? finding.title}</strong><small dir="ltr">Line {finding.sink?.start_line ?? '?'} · {finding.scope?.function ?? 'Unresolved'}</small></span>
                      <span className="candidate-state">CANDIDATE</span>
                    </button>
                  )) : <p>{ar ? 'لا توجد مرشحات في هذا الملف. هذا لا يثبت أنه آمن.' : 'No candidates in this file. This does not prove it is safe.'}</p>}
                </section>
              </div>
            </div>
          </>
        )}
      </section>
    </AppShell>
  );
}
