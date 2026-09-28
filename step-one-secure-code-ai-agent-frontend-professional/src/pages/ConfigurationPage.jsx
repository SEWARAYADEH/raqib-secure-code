import { getConfigurationStatus } from '../api/endpoints';
import AppShell from '../components/AppShell';
import AsyncState from '../components/AsyncState';
import Icon from '../components/Icon';
import StatusBadge from '../components/StatusBadge';
import useAsyncResource from '../hooks/useAsyncResource';
import { useLanguage } from '../i18n';

function StateLine({ label, enabled, ar }) {
  return (
    <div className="security-note">
      <Icon name={enabled ? 'check' : 'info'} />
      <div>
        <strong>{label}</strong>
        <span>{enabled ? (ar ? 'مفعّل' : 'Enabled') : (ar ? 'غير مفعّل' : 'Disabled')}</span>
      </div>
    </div>
  );
}

export default function ConfigurationPage() {
  const { language } = useLanguage();
  const ar = language === 'ar';
  const { data, error, loading, reload } = useAsyncResource(getConfigurationStatus, []);
  const ready = data?.ai?.enabled && data?.ai?.key_configured && data?.ai?.model_configured;

  return (
    <AppShell>
      <section className="narrow-page configuration-page">
        <div className="page-title-row compact">
          <div>
            <span className="eyebrow">{ar ? 'حالة النظام الحقيقية' : 'Live system status'}</span>
            <h1>{ar ? 'إعدادات رقيب' : 'Raqeeb configuration'}</h1>
            <p>{ar
              ? 'تعرض هذه الصفحة حالة الـAPI الفعلية. مفاتيح الخدمات تُضبط على الخادم فقط.'
              : 'This page reads actual API status. Service keys are configured on the server only.'}</p>
          </div>
        </div>

        <AsyncState error={error} loading={loading} loadingLabel={ar ? 'تحميل الحالة…' : 'Loading status…'} onRetry={reload} />

        {data && !loading && !error ? (
          <>
            <section className="settings-block">
              <div className="settings-heading">
                <Icon name="robot" />
                <div>
                  <h2>{ar ? 'ربط مساعد AI' : 'AI advisor connection'}</h2>
                  <p>{ar
                    ? 'المساعد يقترح الفهم والإصلاح فقط. لا يثبت ثغرة ولا يغلق نتيجة.'
                    : 'The advisor assists understanding and repair suggestions. It cannot verify or close a finding.'}</p>
                </div>
                <StatusBadge tone={ready ? 'success' : 'warning'}>{ready ? 'READY' : 'NOT CONFIGURED'}</StatusBadge>
              </div>
              <p>{ar ? 'مكان إضافة المفتاح: إعدادات بيئة الـBackend على الخادم؛ محليًا في الملف ' : 'Add the key to backend server environment settings; locally in '}
                <code dir="ltr">backend/.env</code>. {ar ? 'أضف القيم التالية، ثم أعد تشغيل الـAPI:' : 'Set these values and restart the API:'}</p>
              <pre dir="ltr">OPENAI_API_KEY=&lt;your-secret-key&gt;{'\n'}OPENAI_MODEL=&lt;approved-model&gt;{'\n'}CODEX_ADVISOR_ENABLED=true</pre>
              <p>{ar
                ? 'لا تلصق المفتاح في المتصفح أو Git أو أي ملف داخل واجهة React. الواجهة لا تستلم قيمة المفتاح إطلاقًا.'
                : 'Never paste the key into the browser, Git, or React files. The frontend never receives the key value.'}</p>
              <StateLine ar={ar} enabled={data.ai.key_configured} label={ar ? 'المفتاح موجود على الخادم' : 'Server key configured'} />
              <StateLine ar={ar} enabled={data.ai.model_configured} label={ar ? 'الموديل محدد' : 'Model selected'} />
              <StateLine ar={ar} enabled={data.ai.enabled} label={ar ? 'المساعد مفعّل' : 'Advisor enabled'} />
              <p>{ar ? 'المزوّد: ' : 'Provider: '}{data.ai.provider} · {ar ? 'الموديل: ' : 'Model: '}{data.ai.model ?? 'UNSET'} · {ar ? 'حد السياق: ' : 'Context limit: '}{data.ai.context_limit_characters}</p>
            </section>

            <section className="settings-block">
              <div className="settings-heading"><Icon name="shield" /><div><h2>{ar ? 'الحفظ والحماية' : 'Storage and protection'}</h2></div></div>
              <StateLine ar={ar} enabled={data.storage.enabled} label={ar ? 'حفظ التحليلات' : 'Analysis persistence'} />
              <StateLine ar={ar} enabled={data.email.credentials_present} label={ar ? 'بيانات SMTP موجودة، التسليم غير مثبت' : 'SMTP credentials present; delivery unverified'} />
              <StateLine ar={ar} enabled={data.analysis.osv_advisory_lookup_enabled} label={ar ? 'فحص تنبيهات الاعتماديات OSV' : 'OSV dependency advisory lookup'} />
              <p>{ar ? 'سلامة السجلات: ' : 'Record integrity: '}{data.storage.integrity} · {ar ? 'تشغيل الكود المرفوع: ممنوع' : 'Uploaded code execution: disabled'}</p>
              <p>{ar ? 'السجلات: ' : 'Records: '}{data.storage.analysis_records} · {ar ? 'الملفات المرفوعة: ' : 'Uploaded source: '}{data.storage.uploaded_source_retention}</p>
              <p>{ar ? 'الكتابة فوق الأصل: ' : 'Original overwrite: '}{data.storage.original_overwritten ? 'ENABLED' : 'DISABLED'}</p>
              <p>{ar ? 'اللغات المدعومة فعليًا: ' : 'Actually supported languages: '}{data.analysis.supported_languages.join(' · ')}</p>
            </section>
          </>
        ) : null}
      </section>
    </AppShell>
  );
}
