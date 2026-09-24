import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';

export default function AccountPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    emailVerified,
    rememberDevice,
    setTwoFactorEnabled,
    signOut,
    twoFactorEnabled,
    user,
  } = useAuth();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const activeTab = searchParams.get('tab') || 'profile';
  const [profileName, setProfileName] = useState(user?.name ?? 'Demo Engineer');
  const [saved, setSaved] = useState(false);
  const [confirmDisable, setConfirmDisable] = useState(false);
  const [sessionsCleared, setSessionsCleared] = useState(false);

  const tabs = [
    ['profile', ar ? 'الملف الشخصي' : 'Profile'],
    ['security', ar ? 'الأمان' : 'Security'],
    ['sessions', ar ? 'الجلسات' : 'Sessions'],
  ];

  const doSignOut = () => {
    signOut();
    navigate('/login', { replace: true });
  };

  const disableTwoFactor = () => {
    setTwoFactorEnabled(false);
    setConfirmDisable(false);
  };

  return (
    <AppShell>
      <section className="account-page">
        <header className="page-title-row compact">
          <div>
            <span className="eyebrow">ACCOUNT</span>
            <h1>{ar ? 'الحساب والأمان' : 'Account & security'}</h1>
            <p>
              {ar
                ? 'إدارة بيانات العرض وإعدادات الأمان في واجهة Frontend فقط.'
                : 'Manage demo profile and security UX in the frontend-only experience.'}
            </p>
          </div>
        </header>

        <nav
          aria-label={ar ? 'أقسام الحساب' : 'Account sections'}
          className="account-tabs"
        >
          {tabs.map(([id, label]) => (
            <button
              className={activeTab === id ? 'active' : ''}
              key={id}
              onClick={() => setSearchParams({ tab: id })}
              type="button"
            >
              {label}
            </button>
          ))}
        </nav>

        {activeTab === 'profile' ? (
          <section className="account-section">
            <div className="account-section-heading">
              <div>
                <h2>{ar ? 'الملف الشخصي' : 'Profile'}</h2>
                <p>{ar ? 'بيانات العرض الحالية.' : 'Current frontend demo identity.'}</p>
              </div>
            </div>

            <div className="form-grid two-columns">
              <label className="field-label">
                <span>{ar ? 'الاسم' : 'Name'}</span>
                <input
                  onChange={(event) => {
                    setProfileName(event.target.value);
                    setSaved(false);
                  }}
                  value={profileName}
                />
              </label>

              <label className="field-label">
                <span>{ar ? 'البريد' : 'Email'}</span>
                <input
                  className="technical-input"
                  dir="ltr"
                  readOnly
                  value={user?.email ?? 'engineer@example.com'}
                />
              </label>

              <label className="field-label">
                <span>{ar ? 'لغة الواجهة' : 'Interface language'}</span>
                <input readOnly value={ar ? 'العربية' : 'English'} />
              </label>
            </div>

            <button
              className="button button-primary"
              onClick={() => setSaved(true)}
              type="button"
            >
              {ar ? 'حفظ حالة العرض' : 'Save preview state'}
            </button>

            {saved ? (
              <p className="form-success" role="status">
                {ar
                  ? 'تم الحفظ محليًا في حالة الصفحة فقط.'
                  : 'Saved locally in the page state only.'}
              </p>
            ) : null}
          </section>
        ) : null}

        {activeTab === 'security' ? (
          <section className="account-section">
            <div className="security-setting-row">
              <div>
                <h2>{ar ? 'كلمة المرور' : 'Password'}</h2>
                <p>
                  {ar
                    ? 'تغيير كلمة المرور الحقيقي يحتاج Backend.'
                    : 'Real password change requires the backend.'}
                </p>
              </div>
              <button
                className="button button-secondary"
                onClick={() => navigate('/forgot-password')}
                type="button"
              >
                {ar ? 'عرض مسار الاستعادة' : 'View recovery flow'}
              </button>
            </div>

            <div className="security-setting-row">
              <div>
                <h2>{ar ? 'التحقق من البريد' : 'Email verification'}</h2>
                <p>{ar ? 'حالة تجريبية فقط في الواجهة.' : 'Frontend demo state only.'}</p>
              </div>
              <StatusBadge tone={emailVerified ? 'success' : 'neutral'}>
                {emailVerified
                  ? (ar ? 'موثّق في العرض' : 'Demo verified')
                  : (ar ? 'غير موثّق' : 'Not verified')}
              </StatusBadge>
            </div>

            <div className="security-setting-row">
              <div>
                <h2>{ar ? 'المصادقة الثنائية' : 'Two-factor authentication'}</h2>
                <p>
                  {ar
                    ? 'تجربة TOTP بدون مفاتيح أو تحقق تشفيري داخل React.'
                    : 'TOTP UX without secrets or cryptographic verification inside React.'}
                </p>
              </div>

              <div className="setting-actions">
                <StatusBadge tone={twoFactorEnabled ? 'success' : 'neutral'}>
                  {twoFactorEnabled
                    ? (ar ? 'مفعّلة' : 'Enabled')
                    : (ar ? 'غير مفعّلة' : 'Disabled')}
                </StatusBadge>

                {!twoFactorEnabled ? (
                  <button
                    className="button button-primary"
                    onClick={() => navigate('/two-factor?mode=setup')}
                    type="button"
                  >
                    {ar ? 'تفعيل 2FA' : 'Enable 2FA'}
                  </button>
                ) : (
                  <button
                    className="button button-ghost"
                    onClick={() => setConfirmDisable(true)}
                    type="button"
                  >
                    {ar ? 'تعطيل' : 'Disable'}
                  </button>
                )}
              </div>
            </div>

            {confirmDisable ? (
              <div className="inline-confirm" role="alert">
                <div>
                  <strong>
                    {ar
                      ? 'تعطيل 2FA في حالة Frontend؟'
                      : 'Disable 2FA in frontend state?'}
                  </strong>
                  <p>
                    {ar
                      ? 'لن يتم تغيير أي إعداد أمني حقيقي.'
                      : 'No real security setting will change.'}
                  </p>
                </div>
                <div className="setting-actions">
                  <button
                    className="button button-ghost"
                    onClick={() => setConfirmDisable(false)}
                    type="button"
                  >
                    {ar ? 'إلغاء' : 'Cancel'}
                  </button>
                  <button
                    className="button button-secondary"
                    onClick={disableTwoFactor}
                    type="button"
                  >
                    {ar ? 'تعطيل حالة العرض' : 'Disable demo state'}
                  </button>
                </div>
              </div>
            ) : null}

            <div className="security-setting-row">
              <div>
                <h2>{ar ? 'رموز الاسترداد' : 'Recovery codes'}</h2>
                <p>
                  {ar
                    ? 'تظهر بعد إعداد 2FA في مسار العرض فقط.'
                    : 'Shown after 2FA setup in the demo flow only.'}
                </p>
              </div>
              <StatusBadge tone={twoFactorEnabled ? 'info' : 'neutral'}>
                {twoFactorEnabled
                  ? (ar ? 'متاحة في مسار الإعداد' : 'Available in setup flow')
                  : (ar ? 'غير متاحة' : 'Unavailable')}
              </StatusBadge>
            </div>
          </section>
        ) : null}

        {activeTab === 'sessions' ? (
          <section className="account-section">
            <div className="account-section-heading">
              <div>
                <h2>{ar ? 'الجلسات' : 'Sessions'}</h2>
                <p>
                  {ar
                    ? 'بيانات Demo داخل الواجهة، بدون ادعاء موقع دقيق.'
                    : 'Demo metadata only, with no precise-location claim.'}
                </p>
              </div>
            </div>

            <div className="session-list">
              <article>
                <div className="session-icon"><Icon name="user" /></div>
                <div>
                  <strong>Chrome · Windows</strong>
                  <span>
                    {ar ? 'الجلسة الحالية · نشطة الآن' : 'Current session · active now'}
                    {rememberDevice
                      ? (ar ? ' · تذكّر الجهاز مفعّل للعرض' : ' · remember preference on')
                      : ''}
                  </span>
                </div>
                <StatusBadge tone="success">{ar ? 'حالية' : 'Current'}</StatusBadge>
              </article>

              {!sessionsCleared ? (
                <article>
                  <div className="session-icon"><Icon name="user" /></div>
                  <div>
                    <strong>Browser session · Demo</strong>
                    <span>
                      {ar
                        ? 'بيانات عرض غير مرتبطة بجهاز حقيقي'
                        : 'Preview metadata not tied to a real device'}
                    </span>
                  </div>
                  <StatusBadge tone="neutral">Demo</StatusBadge>
                </article>
              ) : null}
            </div>

            {!sessionsCleared ? (
              <button
                className="button button-secondary"
                onClick={() => setSessionsCleared(true)}
                type="button"
              >
                {ar
                  ? 'تسجيل خروج الجلسات الأخرى — Demo'
                  : 'Sign out other sessions — demo'}
              </button>
            ) : (
              <p className="form-success" role="status">
                {ar
                  ? 'تمت إزالة الجلسات التجريبية من الواجهة.'
                  : 'Other demo sessions were removed from the interface.'}
              </p>
            )}
          </section>
        ) : null}

        <section className="account-danger-zone">
          <div>
            <h2>{ar ? 'تسجيل الخروج' : 'Sign out'}</h2>
            <p>
              {ar
                ? 'يمسح حالة المصادقة التجريبية ويرجع إلى شاشة الدخول.'
                : 'Clears the mock authenticated state and returns to sign in.'}
            </p>
          </div>
          <button className="button button-ghost" onClick={doSignOut} type="button">
            <Icon name="logout" size={17} />
            {ar ? 'تسجيل الخروج' : 'Sign out'}
          </button>
        </section>
      </section>
    </AppShell>
  );
}
