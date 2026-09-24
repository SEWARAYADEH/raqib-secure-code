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
  const [profile, setProfile] = useState('deep');
  const [standardsPack, setStandardsPack] = useState('core-web');
  const [includePaths, setIncludePaths] = useState('');
  const [excludePaths, setExcludePaths] = useState('');
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
            profile,
            standardsPack,
            includePaths,
            excludePaths,
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
                ? 'اختر ملف كود أو مشروع ZIP. يتم التحقق من المدخل وتحليله ساكنًا دون تشغيله.'
                : 'Choose a code file or project ZIP. Input is validated and statically analyzed without execution.'}
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
                      : ar ? 'مشروع كامل' : 'Full project'}
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
                      ? ar ? 'ملف واحد للتحليل العميق.' : 'One file for focused analysis.'
                      : ar ? 'ملف ZIP للمشروع ضمن حدود الاستخراج الآمن.' : 'Project ZIP with secure extraction limits.'}
                </small>
              </label>
            </fieldset>

            <fieldset className="form-section">
              <legend>{ar ? '3. إعدادات الفحص' : '3. Scan preparation'}</legend>
              <div className="form-grid two-columns">
                <label className="field-label">
                  <span>{ar ? 'ملف الفحص' : 'Scan profile'}</span>
                  <select onChange={(event) => setProfile(event.target.value)} value={profile}>
                    {options.scanProfiles.map((item) => (
                      <option key={item.id} value={item.id}>
                        {ar
                          ? item.id === 'quick'
                            ? 'سريع'
                            : item.id === 'standard'
                              ? 'قياسي'
                              : 'عميق'
                          : item.label}
                      </option>
                    ))}
                  </select>
                  <small>{ar ? 'يُحفظ كخيار واجهة حتى يدعمه عقد التحليل.' : 'Stored as a UI preference until supported by the analysis contract.'}</small>
                </label>

                <label className="field-label">
                  <span>{ar ? 'حزمة المعايير' : 'Standards pack'}</span>
                  <select
                    onChange={(event) => setStandardsPack(event.target.value)}
                    value={standardsPack}
                  >
                    {options.standardsPacks.map((item) => (
                      <option key={item.id} value={item.id}>{item.label}</option>
                    ))}
                  </select>
                  <small>{ar ? 'لا يغيّر نتيجة المحرك الحالي.' : 'Does not alter the current engine result.'}</small>
                </label>
              </div>

              <div className="form-grid two-columns">
                <label className="field-label">
                  <span>{ar ? 'المسارات المشمولة' : 'Include paths'}</span>
                  <input
                    className="technical-input"
                    dir="ltr"
                    onChange={(event) => setIncludePaths(event.target.value)}
                    placeholder="app/, src/"
                    type="text"
                    value={includePaths}
                  />
                </label>

                <label className="field-label">
                  <span>{ar ? 'المسارات المستثناة' : 'Exclude paths'}</span>
                  <input
                    className="technical-input"
                    dir="ltr"
                    onChange={(event) => setExcludePaths(event.target.value)}
                    placeholder="vendor/, dist/"
                    type="text"
                    value={excludePaths}
                  />
                </label>
              </div>

              <p className="backend-contract-note">
                <Icon name="info" size={18} />
                {ar
                  ? 'المسارات والملف الأمني إعدادات مستقبلية ولا تُرسل حالياً؛ نوع الملف وحجمه ومحتواه تتحقق منها الـAPI.'
                  : 'Path and profile controls are future settings and are not submitted yet; the API validates file type, size, and content.'}
              </p>
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
