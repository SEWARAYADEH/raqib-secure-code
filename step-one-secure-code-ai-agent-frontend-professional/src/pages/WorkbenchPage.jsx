import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWorkbench } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import ProjectPassport from '../components/ProjectPassport';
import WorkbenchCodePane from '../components/WorkbenchCodePane';
import WorkbenchExplorer from '../components/WorkbenchExplorer';
import WorkbenchInspector from '../components/WorkbenchInspector';
import WorkflowBar from '../components/WorkflowBar';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

function stageOperation(stage, liveOperation, ar) {
  const map = {
    fingerprint: {
      title: ar ? 'تحديد بصمة المشروع' : 'Building the project fingerprint',
      action: ar
        ? 'تحديد اللغة والإطار وقاعدة البيانات والبنية ونقاط الدخول.'
        : 'Detecting language, framework, database, architecture, and entry points.',
      discovery: ar
        ? 'تم تحديد Python / Flask وبنية تطبيق ويب طبقية.'
        : 'Python / Flask and a layered web architecture are identified.',
      why: ar
        ? 'الفحص الصحيح يبدأ بفهم نوع الكود وسياقه قبل إصدار أي حكم أمني.'
        : 'A meaningful security review starts by understanding code type and context.',
    },
    understand: {
      title: ar ? 'فهم وظيفة الكود' : 'Understanding what the code does',
      action: ar
        ? 'ربط الملفات بالدوال ووظيفة كل جزء قبل الحكم على المخاطر.'
        : 'Connecting files, functions, and purpose before judging security risk.',
      discovery: ar
        ? 'تم ربط Route المستخدم بخدمة قراءة بيانات المستخدم.'
        : 'A user route is linked to the user retrieval service.',
      why: ar
        ? 'السطر نفسه قد يكون آمنًا أو خطيرًا حسب المسار والصلاحيات.'
        : 'The same line can be safe or risky depending on flow and authorization context.',
    },
    scan: {
      title: ar ? 'مراجعة نتائج الـScanner' : 'Reviewing scanner coverage',
      action: ar
        ? 'عرض التغطية والقواعد والنتائج وربطها بالملفات والدوال.'
        : 'Showing coverage, rules, findings, and their mapping to files and functions.',
      discovery: ar
        ? 'ثلاث نتائج تحتاج مراجعة ضمن التغطية الحالية.'
        : 'Three findings require review within the current coverage.',
      why: ar
        ? 'الـFinding لا تبقى Alert منفصلة؛ يجب ربطها بالكود والسياق.'
        : 'A finding should not stay isolated; it must be tied to code and context.',
    },
    investigate: ar
      ? {
          title: 'تتبع المعرّف عبر حدود الصلاحيات',
          action: 'تتبع user_id من مسار Flask إلى UserService ثم طبقة المستودع.',
          discovery: 'المصادقة موجودة، لكن التحقق من ملكية المورد غير ظاهر في المسار.',
          why: 'المصادقة تثبت الهوية، لكنها لا تثبت حق الوصول إلى مورد مستخدم آخر.',
        }
      : liveOperation,
    transform: {
      title: ar ? 'تحويل الضعف إلى Secure Candidate' : 'Building a secure candidate',
      action: ar
        ? 'عرض Root Cause والكود الضعيف والنسخة المقترحة بشكل قابل للمراجعة.'
        : 'Showing root cause, weak code, and the proposed candidate in a reviewable diff.',
      discovery: ar
        ? 'التعديل المقترح يضيف قرار Authorization قبل إرجاع المورد.'
        : 'The proposed change adds an authorization decision before returning the resource.',
      why: ar
        ? 'الإصلاح يجب أن يعالج السبب الجذري، وليس فقط نتيجة الـScanner.'
        : 'A fix must address the root cause, not merely silence a scanner result.',
    },
    verify: {
      title: ar ? 'إعادة الفحص وإثبات النتيجة' : 'Re-scanning and proving the result',
      action: ar
        ? 'مراجعة الاختبار الوظيفي وReplay وRe-scan وRe-trace.'
        : 'Reviewing functional test, replay, re-scan, and re-trace evidence.',
      discovery: ar
        ? 'قرار الإغلاق يعتمد على Evidence وليس على اقتراح AI.'
        : 'Closure depends on evidence, not on the AI proposal.',
      why: ar
        ? 'التحسن الأمني يجب أن يكون قابلًا للمراجعة وإعادة الاختبار.'
        : 'Security improvement must be reviewable and reproducible.',
    },
    report: {
      title: ar ? 'تجميع التقرير الأمني' : 'Preparing the security report',
      action: ar
        ? 'تنظيم النتائج والتغطية والإصلاحات والأدلة في تقرير واضح.'
        : 'Organizing findings, coverage, remediation, and evidence into a clear report.',
      discovery: ar
        ? 'التقرير يوضح ما تم إصلاحه وما بقي وما لم يتم إثباته.'
        : 'The report separates remediated, remaining, and not-yet-proven items.',
      why: ar
        ? 'الخبير يحتاج سجلًا يمكن لشخص ثالث مراجعته.'
        : 'Experts need a record that a third party can review.',
    },
  };

  return map[stage] ?? map.fingerprint;
}

export default function WorkbenchPage() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data, error, loading, reload } = useAsyncResource(getWorkbench, []);
  const [selectedFileId, setSelectedFileId] = useState('users-route');
  const [selectedFindingId, setSelectedFindingId] = useState('SC-001');
  const [selectedFunction, setSelectedFunction] = useState('get_user');
  const [zoom, setZoom] = useState(1);
  const [showExplorer, setShowExplorer] = useState(true);
  const [showInspector, setShowInspector] = useState(true);
  const [workflowId, setWorkflowId] = useState('fingerprint');
  const [fileSearch, setFileSearch] = useState('');
  const [fileFilter, setFileFilter] = useState('all');

  const file = useMemo(() => {
    if (!data?.files?.length) return null;
    return data.files.find((item) => item.id === selectedFileId) ?? data.files[0];
  }, [data, selectedFileId]);

  const finding = useMemo(() => {
    if (!data?.findings?.length || !file) return null;
    const fileFindings = data.findings.filter((item) => item.fileId === file.id);
    return fileFindings.find((item) => item.id === selectedFindingId) ?? fileFindings[0] ?? null;
  }, [data, file, selectedFindingId]);

  const filteredFiles = useMemo(() => {
    if (!data?.files) return [];
    const query = fileSearch.trim().toLowerCase();

    return data.files.filter((item) => {
      const matchesQuery = !query
        || item.name.toLowerCase().includes(query)
        || item.path.toLowerCase().includes(query);
      const matchesStatus = fileFilter === 'all'
        || (fileFilter === 'issues' && item.status !== 'safe')
        || (fileFilter === 'safe' && item.status === 'safe');
      return matchesQuery && matchesStatus;
    });
  }, [data, fileFilter, fileSearch]);

  const codeLines = file?.code.split('\n') ?? [];
  const operation = stageOperation(workflowId, data?.liveOperation, ar);
  const stageIndex = data?.workflow.findIndex((stage) => stage.id === workflowId) ?? 0;

  const selectFile = (nextFile) => {
    setSelectedFileId(nextFile.id);
    const nextFinding = data.findings.find((item) => item.fileId === nextFile.id);
    setSelectedFindingId(nextFinding?.id ?? '');
    setSelectedFunction(nextFile.functions[0]?.name ?? '');
    if (stageIndex > 1) setWorkflowId('understand');
  };

  const selectFunction = (fn) => {
    setSelectedFunction(fn.name);
    const fnFinding = data.findings.find(
      (item) => item.fileId === file.id && item.function === fn.name,
    );
    setSelectedFindingId(fnFinding?.id ?? '');
  };

  const chooseFinding = (item) => {
    setSelectedFileId(item.fileId);
    setSelectedFindingId(item.id);
    setSelectedFunction(item.function ?? '');
    setWorkflowId('investigate');
  };

  const focusCode = () => {
    if (!showExplorer && !showInspector) {
      setShowExplorer(true);
      setShowInspector(true);
      return;
    }
    setShowExplorer(false);
    setShowInspector(false);
  };

  const gridClass = [
    'secure-workbench',
    showExplorer ? '' : 'without-explorer',
    showInspector ? '' : 'without-inspector',
  ].filter(Boolean).join(' ');

  return (
    <AppShell>
      <AsyncState
        error={error}
        loading={loading}
        loadingLabel={ar ? 'تحميل مساحة العمل…' : 'Loading secure workbench…'}
        onRetry={reload}
      />

      {!loading && !error && data && file ? (
        <>
          <ProjectPassport project={data.passport} />

          <section className="workbench-commandbar">
            <WorkflowBar
              currentId={workflowId}
              onSelect={setWorkflowId}
              stages={data.workflow}
            />
            <div className="command-actions">
              <button
                aria-pressed={showExplorer}
                className={`icon-button${showExplorer ? ' active' : ''}`}
                onClick={() => setShowExplorer((value) => !value)}
                title={ar ? 'إظهار أو إخفاء الملفات' : 'Toggle project explorer'}
                type="button"
              >
                <Icon name="projects" />
              </button>
              <button
                className="icon-button"
                onClick={() => setZoom((value) => Math.max(0.8, value - 0.1))}
                title={ar ? 'تصغير الكود' : 'Zoom out'}
                type="button"
              >
                <Icon name="zoomOut" />
              </button>
              <span className="zoom-value">{Math.round(zoom * 100)}%</span>
              <button
                className="icon-button"
                onClick={() => setZoom((value) => Math.min(1.5, value + 0.1))}
                title={ar ? 'تكبير الكود' : 'Zoom in'}
                type="button"
              >
                <Icon name="zoomIn" />
              </button>
              <button
                className="icon-button"
                onClick={focusCode}
                title={ar ? 'وضع التركيز' : 'Focus code'}
                type="button"
              >
                <Icon name="expand" />
              </button>
              <button
                aria-pressed={showInspector}
                className={`icon-button${showInspector ? ' active' : ''}`}
                onClick={() => setShowInspector((value) => !value)}
                title={ar ? 'إظهار أو إخفاء Inspector' : 'Toggle inspector'}
                type="button"
              >
                <Icon name="panel" />
              </button>
            </div>
          </section>

          <section className="live-operation">
            <div className="live-operation-icon"><Icon name="robot" /></div>
            <div className="live-operation-main">
              <span className="eyebrow">RAQEEB · <bdi dir="ltr">{workflowId.toUpperCase()}</bdi></span>
              <strong>{operation.title}</strong>
              <p>{operation.action}</p>
            </div>
            <div className="live-operation-proof">
              <span>{ar ? 'ما تم اكتشافه' : 'What was discovered'}</span>
              <strong>{operation.discovery}</strong>
              <small>{operation.why}</small>
            </div>
          </section>

          <section className={gridClass}>
            {showExplorer ? (
              <WorkbenchExplorer
                ar={ar}
                data={data}
                file={file}
                fileFilter={fileFilter}
                fileSearch={fileSearch}
                filteredFiles={filteredFiles}
                onChooseFinding={chooseFinding}
                onFileFilter={setFileFilter}
                onFileSearch={setFileSearch}
                onSelectFile={selectFile}
                onSelectFunction={selectFunction}
                selectedFindingId={selectedFindingId}
                selectedFunction={selectedFunction}
              />
            ) : null}

            <WorkbenchCodePane
              ar={ar}
              codeLines={codeLines}
              file={file}
              finding={finding}
              workflowId={workflowId}
              zoom={zoom}
            />

            {showInspector ? (
              <WorkbenchInspector
                ar={ar}
                data={data}
                file={file}
                finding={finding}
                onOpenReport={() => navigate(`/projects/${data.passport.id}/report`)}
                onStage={setWorkflowId}
                selectedFunction={selectedFunction}
                workflowId={workflowId}
              />
            ) : null}
          </section>
        </>
      ) : null}
    </AppShell>
  );
}
