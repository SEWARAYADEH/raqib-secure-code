import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createAnalysis, getAnalysisOptions } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

function bytesToLabel(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 KB';
  if (bytes < 1024 * 1024) return `${Math.ceil(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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

  const selectedScope = useMemo(() => {
    return options?.scopes.find((item) => item.id === scope) ?? options?.scopes[0];
  }, [options, scope]);

  const onFile = (event) => {
    setSelectedFile(event.target.files?.[0] ?? null);
    setFormError('');
  };

  const submit = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setFormError(ar ? 'اختر ملفًا أو مشروعًا أولًا.' : 'Choose a file or project first.');
      return;
    }

    const limit = scope === 'project' ? 20 * 1024 * 1024 : 2 * 1024 * 1024;
    if (selectedFile.size === 0 || selectedFile.size > limit) {
      setFormError(ar
        ? `حجم الملف يجب أن يكون أكبر من صفر وأقل من ${bytesToLabel(limit)}.`
        : `File size must be greater than zero and at most ${bytesToLabel(limit)}.`);
      return;
    }

    setSubmitting(true);
    setFormError('');

    try {
      const analysis = await createAnalysis({
        file: selectedFile,
        scope,
      });
      setSubmitting(false);
      const resultPath = analysis.record?.persisted && analysis.record.analysis_id
        ? `/analysis/progress/${encodeURIComponent(analysis.record.analysis_id)}`
        : '/analysis/progress';
      navigate(resultPath, {
        state: {
          analysis,
          input: {
            scope,
            fileName: selectedFile.name,
          },
        },
      });
    } catch (submitError) {
      setSubmitting(false);
      setFormError(
        submitError instanceof Error
          ? submitError.message
          : (ar ? 'تعذر بدء التحليل.' : 'Unable to start analysis.'),
      );
    }
  };

  return (
    <AppShell>
      <section className="narrow-page">
        <div className="page-title-row compact">
          <div>
            <span className="eyebrow">{ar ? 'مدخل واحد واضح' : 'Focused intake'}</span>
            <h1>{ar ? 'تحليل أمني جديد' : 'New security analysis'}</h1>
            <p>
              {ar
                ? 'اختر ملف Python أو JavaScript/JSX، أو مشروع ZIP بهذه اللغات. يفحص النظام المحتوى والبنية دون تشغيل الكود.'
                : 'Choose a Python or JavaScript/JSX file, or a ZIP project in these languages. Content and structure are analyzed without execution.'}
            </p>
          </div>
        </div>

        <AsyncState
          error={error}
          loading={loading}
          loadingLabel={ar ? 'تحميل خيارات التحليل…' : 'Loading analysis options…'}
          onRetry={reload}
        />

        {!loading && !error && options ? (
          <form className="analysis-form" onSubmit={submit}>
            <fieldset className="form-section">
              <legend>{ar ? '1. ما الذي تريد تحليله؟' : '1. What do you want to analyze?'}</legend>
              <div className="scope-switch">
                {options.scopes.map((item) => (
                  <button
                    aria-pressed={scope === item.id}
                    className={scope === item.id ? 'active' : ''}
                    key={item.id}
                    onClick={() => {
                      setScope(item.id);
                      setSelectedFile(null);
                    }}
                    type="button"
                  >
                    <Icon name={item.id === 'file' ? 'file' : 'projects'} />
                    {item.id === 'file'
                      ? ar ? 'ملف كود' : 'Code file'
                      : ar ? 'مشروع ZIP' : 'ZIP project'}
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset className="form-section">
              <legend>{ar ? '2. اختر المدخل' : '2. Choose the input'}</legend>
              <label className="upload-zone">
                <input
                  accept={selectedScope?.accept}
                  onChange={onFile}
                  type="file"
                />
                <span className="upload-icon"><Icon name="upload" size={28} /></span>
                <strong>
                  {selectedFile?.name ? <bdi dir="ltr">{selectedFile.name}</bdi> : (ar ? 'اختر من جهازك' : 'Choose from your device')}
                </strong>
                <small>
                  {selectedFile
                    ? <span className="technical-value">{selectedFile.name} · {bytesToLabel(selectedFile.size)}</span>
                    : scope === 'file'
                      ? ar ? 'ملف واحد للتحليل الساكن.' : 'One file for static analysis.'
                      : ar ? 'ملف ZIP للمشروع ضمن حدود الاستخراج الآمن.' : 'Project ZIP with secure extraction limits.'}
                </small>
              </label>
            </fieldset>

            {formError ? <p className="form-error" role="alert">{formError}</p> : null}

            <button className="button button-primary button-wide" disabled={submitting} type="submit">
              <Icon name="shield" />
              {submitting
                ? ar ? 'تحليل المدخل الآمن…' : 'Analyzing secure input…'
                : ar ? 'بدء التحليل الآمن' : 'Start secure analysis'}
            </button>
          </form>
        ) : null}
      </section>
    </AppShell>
  );
}
