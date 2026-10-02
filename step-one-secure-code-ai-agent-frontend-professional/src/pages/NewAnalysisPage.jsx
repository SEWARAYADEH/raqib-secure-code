import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createAnalysis, getAnalysisOptions } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

const FORMATS = [
  ['Python', '.py'], ['JavaScript', '.js'],
  ['JavaScript JSX', '.jsx'], ['Full Project', '.zip'],
];

function formatSize(bytes) {
  return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function preliminaryLanguage(fileName) {
  const extension = fileName.split('.').pop()?.toLowerCase();
  if (extension === 'py') return 'Python';
  if (extension === 'js') return 'JavaScript';
  if (extension === 'jsx') return 'JavaScript JSX';
  return 'Unknown until content analysis';
}

function packLabel(pack) {
  if (pack.can_verify_exploitability && pack.can_generate_verified_patch && pack.can_close) return 'Verification & Repair Available';
  return pack.status === 'PARTIAL_STATIC_CANDIDATES' ? 'Analysis Available' : 'Coming / In Development';
}

export default function NewAnalysisPage() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data: options, error, loading, reload } = useAsyncResource(getAnalysisOptions, []);
  const [scope, setScope] = useState('file');
  const [selectedFile, setSelectedFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const selectedScope = options?.scopes?.find((item) => item.id === scope);
  const accepted = new Set(options?.scopes?.flatMap((item) => item.accept.split(',')) ?? []);

  async function submit(event) {
    event.preventDefault();
    setFormError('');
    if (!selectedFile) {
      setFormError(ar ? 'اختر ملفًا أولًا.' : 'Choose a file first.');
      return;
    }
    if (selectedFile.size === 0 || selectedFile.size > selectedScope.max_bytes) {
      setFormError(ar ? `الحجم المسموح: أكبر من صفر وحتى ${formatSize(selectedScope.max_bytes)}.` : `Allowed size: above zero and up to ${formatSize(selectedScope.max_bytes)}.`);
      return;
    }
    try {
      setSubmitting(true);
      const analysis = await createAnalysis({ file: selectedFile, scope });
      const path = analysis.record?.persisted && analysis.record.analysis_id
        ? `/analysis/progress/${encodeURIComponent(analysis.record.analysis_id)}` : '/analysis/progress';
      navigate(path, { state: { analysis, input: { scope, fileName: selectedFile.name } } });
    } catch (failure) {
      setFormError(failure instanceof Error ? failure.message : (ar ? 'تعذر التحليل.' : 'Analysis failed.'));
    } finally {
      setSubmitting(false);
    }
  }

  return <AppShell><section className="intake-page">
    <header className="intake-heading"><span className="eyebrow">SAFE CODE INTAKE</span><h1>{ar ? 'ابدأ بتحليل مشروعك' : 'Analyze your project'}</h1><p>{ar ? 'ملف كود أو ZIP. رقيب يقرأ المحتوى والبنية دون تشغيل الكود.' : 'Code file or ZIP. Raqeeb reads content and structure without executing it.'}</p></header>
    <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل أنواع الملفات…' : 'Loading supported formats…'} onRetry={reload} />
    {!loading && !error && options && <>
      <form className="intake-panel" onSubmit={submit}>
        <div className="intake-scope" role="group" aria-label={ar ? 'نوع الرفع' : 'Upload type'}>
          {options.scopes.map((item) => <button aria-pressed={scope === item.id} className={scope === item.id ? 'active' : ''} key={item.id} onClick={() => { setScope(item.id); setSelectedFile(null); setFormError(''); }} type="button">{item.id === 'file' ? 'Code File' : 'ZIP Project'}<small>{item.accept.replaceAll(',', ' · ')}</small></button>)}
        </div>
        <label className="intake-drop"><span className="intake-upload-icon" aria-hidden="true">↑</span><strong>{selectedFile ? <bdi dir="ltr">{selectedFile.name}</bdi> : (ar ? 'اختر ملفًا من جهازك' : 'Choose a file from your device')}</strong><small>{ar ? 'فحص محتوى وبنية · دون تنفيذ أو تعديل الأصل' : 'Content and structure analysis · no execution or overwrite'}</small><input accept={selectedScope?.accept} onChange={(event) => { setSelectedFile(event.target.files?.[0] ?? null); setFormError(''); }} type="file" /></label>
        {selectedFile && <dl className="intake-file-facts"><div><dt>{ar ? 'الملف' : 'File'}</dt><dd dir="ltr">{selectedFile.name}</dd></div><div><dt>{ar ? 'النوع' : 'Type'}</dt><dd>{scope === 'project' ? 'ZIP Project' : 'Code File'}</dd></div><div><dt>{ar ? 'الحجم' : 'Size'}</dt><dd>{formatSize(selectedFile.size)}</dd></div><div><dt>{ar ? 'اللغة المتوقعة' : 'Expected language'}</dt><dd>{scope === 'project' ? 'Unknown until content analysis' : preliminaryLanguage(selectedFile.name)} <small>{ar ? 'أولي فقط' : 'preliminary'}</small></dd></div><div><dt>{ar ? 'التحليل' : 'Analysis'}</dt><dd>Static · No execution</dd></div></dl>}
        {formError && <p className="form-error" role="alert">{formError}</p>}
        {submitting && <div className="intake-activity" role="status">
          <span className="intake-activity-ring" aria-hidden="true" />
          <div><strong>{ar ? 'طلب التحليل قيد المعالجة' : 'Analysis request in progress'}</strong><small>{ar ? 'ننتظر نتيجة المحرك؛ حالة كل مرحلة ستظهر من البيانات المحفوظة بعد اكتمال الطلب.' : 'Waiting for the engine response. Stage results will come from the saved analysis.'}</small></div>
        </div>}
        <button className="button button-primary intake-submit" disabled={submitting} type="submit">{submitting ? (ar ? 'جارٍ التحليل…' : 'Analyzing…') : (ar ? 'ابدأ التحليل' : 'Start analysis')}</button>
      </form>
      <section className="intake-support"><h2>{ar ? 'الملفات المقبولة الآن' : 'Accepted now'}</h2><div className="intake-formats">{FORMATS.filter(([, extension]) => accepted.has(extension)).map(([name, extension]) => <div key={extension}><strong>{name}</strong><code>{extension}</code></div>)}</div><p>{ar ? 'رقيب يفحص محتوى المشروع وبنيته، مش مجرد اسم الملف أو امتداده.' : 'Raqeeb checks project content and structure, not just the filename or extension.'}</p></section>
      <section className="intake-support"><h2>{ar ? 'أهم المشاكل اللي بنركز عليها' : 'Focused security problems'}</h2><div className="intake-packs">{options.security_packs.map((pack) => <div key={pack.id}><strong>{pack.display_name}</strong><span>{packLabel(pack)}</span></div>)}</div><p>{ar ? 'حالة الدعم من الخادم؛ لم يثبت أي إصلاح أو إغلاق تلقائي بعد.' : 'Backend support status; no automatic repair or closure is claimed.'}</p></section>
    </>}
  </section></AppShell>;
}
