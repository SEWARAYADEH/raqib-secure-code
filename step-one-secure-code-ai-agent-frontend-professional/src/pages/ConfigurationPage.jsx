import { useEffect, useState } from 'react';
import { getConfiguration } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

export default function ConfigurationPage() {
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data, error, loading, reload } = useAsyncResource(getConfiguration, []);
  const [model, setModel] = useState('');
  const [profile, setProfile] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!data) return;
    setModel(data.aiModel);
    setProfile(data.scanProfile);
  }, [data]);

  const applyPreview = () => {
    setSaving(true);
    setSaved(false);

    window.setTimeout(() => {
      setSaving(false);
      setSaved(true);
    }, 180);
  };

  return (
    <AppShell>
      <section className="narrow-page configuration-page">
        <div className="page-title-row compact">
          <div>
            <span className="eyebrow">{ar ? 'ضبط الواجهة' : 'Frontend configuration'}</span>
            <h1>{ar ? 'إعدادات رقيب' : 'Raqeeb configuration'}</h1>
            <p>
              {ar
                ? 'مكان واضح لربط AI وسياسات الفحص لاحقًا. لا أسرار ولا مفاتيح داخل React.'
                : 'A clear place for future AI and scan-policy integration. No secrets or keys belong in React.'}
            </p>
          </div>
        </div>

        <AsyncState
          error={error}
          loading={loading}
          loadingLabel={ar ? 'تحميل الإعدادات…' : 'Loading configuration…'}
          onRetry={reload}
        />

        {!loading && !error && data ? (
          <>
            <section className="settings-block">
              <div className="settings-heading">
                <Icon name="robot" />
                <div>
                  <h2>{ar ? 'محرك الذكاء الاصطناعي' : 'AI engine'}</h2>
                  <p>
                    {ar
                      ? 'AI مساعد في الفهم والربط واقتراح الإصلاح، وليس صاحب قرار الإغلاق.'
                      : 'AI assists understanding, correlation, and fix candidates; it does not own closure.'}
                  </p>
                </div>
              </div>

              <div className="form-grid two-columns">
                <label className="field-label">
                  <span>{ar ? 'المزوّد' : 'Provider'}</span>
                  <input className="technical-input" dir="ltr" readOnly value={data.aiProvider} />
                </label>
                <label className="field-label">
                  <span>{ar ? 'الموديل' : 'Model'}</span>
                  <input className="technical-input" dir="ltr" onChange={(event) => setModel(event.target.value)} value={model} />
                  <small>
                    {ar
                      ? 'اسم الموديل فقط. الـAPI key يجب أن يبقى في الـBackend.'
                      : 'Model identifier only. API keys must remain in the backend.'}
                  </small>
                </label>
              </div>

              <div className="role-pills technical-pills">
                {data.aiRoles.map((role) => <span key={role}>{role}</span>)}
              </div>

              <div className="security-note">
                <Icon name="shield" />
                <div>
                  <strong className="technical-value">{data.connectionState}</strong>
                  <span>{ar
                    ? 'مفاتيح الـAPI وبيانات اعتماد النموذج يجب أن تبقى في الـBackend، وليس داخل React.'
                    : data.note}</span>
                </div>
              </div>
            </section>

            <section className="settings-block">
              <div className="settings-heading">
                <Icon name="scan" />
                <div>
                  <h2>{ar ? 'سياسة الفحص' : 'Scan policy'}</h2>
                  <p>
                    {ar
                      ? 'هذه قيمة Frontend preview. تعريف Quick / Standard / Deep سيأتي من عقد الـBackend.'
                      : 'This is a frontend preview value. Quick / Standard / Deep behavior will come from the backend contract.'}
                  </p>
                </div>
              </div>

              <div className="form-grid two-columns">
                <label className="field-label">
                  <span>{ar ? 'ملف الفحص' : 'Scan profile'}</span>
                  <select onChange={(event) => setProfile(event.target.value)} value={profile}>
                    {data.scanProfiles.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </label>
                <label className="field-label">
                  <span>{ar ? 'حزمة المعايير' : 'Standards pack'}</span>
                  <input className="technical-input" dir="ltr" readOnly value={data.standardsPack} />
                </label>
              </div>
            </section>

            <button
              className="button button-primary button-wide"
              disabled={saving}
              onClick={applyPreview}
              type="button"
            >
              {saving
                ? ar ? 'تطبيق العرض محليًا…' : 'Applying preview locally…'
                : ar ? 'تطبيق العرض التجريبي' : 'Apply preview'}
            </button>

            {saved ? (
              <p className="success-inline" role="status">
                <Icon name="check" />
                {ar
                  ? 'تم تطبيق الإعداد داخل حالة الواجهة الحالية فقط. لم يتم إرسال أي شيء إلى Backend.'
                  : 'Applied to the current frontend state only. Nothing was sent to a backend.'}
              </p>
            ) : null}
          </>
        ) : null}
      </section>
    </AppShell>
  );
}
