import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { setAccountPassword } from '../api/endpoints';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';

export default function AccountPage() {
  const navigate = useNavigate();
  const { passwordConfigured, passwordResetAllowed, refreshSession, signOut, user } = useAuth();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [currentPassword, setCurrentPassword] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function savePassword(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    if (password !== confirmation) {
      setError(ar ? 'تأكيد كلمة المرور لا يطابقها.' : 'Password confirmation does not match.');
      return;
    }
    try {
      setSubmitting(true);
      await setAccountPassword({ password, currentPassword });
      await refreshSession();
      setCurrentPassword('');
      setPassword('');
      setConfirmation('');
      setMessage(ar ? 'حُفظت كلمة المرور على الخادم. يمكنك استخدامها في الدخول القادم.' : 'Password saved on the server. You can use it next time.');
    } catch (failure) {
      setError(failure.code === 'CURRENT_PASSWORD_INVALID'
        ? (ar ? 'كلمة المرور الحالية غير صحيحة.' : 'Current password is incorrect.')
        : failure.code === 'PASSWORD_POLICY_REJECTED'
          ? (ar ? 'استخدم 12 حرفًا على الأقل مع حرف كبير وصغير ورقم ورمز.' : 'Use at least 12 characters, uppercase and lowercase letters, a number, and a symbol.')
          : (ar ? 'تعذر حفظ كلمة المرور.' : 'Could not save the password.'));
    } finally {
      setSubmitting(false);
    }
  }

  function logOut() {
    signOut();
    navigate('/login', { replace: true });
  }

  return (
    <AppShell>
      <section className="narrow-page configuration-page">
        <div className="page-title-row compact">
          <div>
            <span className="eyebrow">ACCOUNT SECURITY</span>
            <h1>{ar ? 'الحساب والأمان' : 'Account and security'}</h1>
            <p>{ar ? 'هوية الجلسة من الخادم. لا توجد إعدادات أمنية تجريبية هنا.' : 'Session identity comes from the server. No simulated security settings are shown.'}</p>
          </div>
        </div>

        <section className="account-section">
          <h2>{ar ? 'البريد الموثّق' : 'Verified email'}</h2>
          <p dir="ltr"><strong>{user?.email}</strong></p>
          <p>{ar ? 'تبقى جلسة الدخول صالحة حتى سبعة أيام على هذا المتصفح، أو إلى أن تسجّل الخروج. تغيير عنوان الموقع بين localhost و127.0.0.1 ينشئ جلسة مختلفة.' : 'Your session lasts up to seven days in this browser, or until you sign out. localhost and 127.0.0.1 use separate cookies.'}</p>
        </section>

        <section className="account-section">
          <h2>{passwordConfigured ? (ar ? 'تغيير كلمة المرور' : 'Change password') : (ar ? 'إنشاء كلمة مرور للدخول' : 'Create sign-in password')}</h2>
          <p>{ar ? 'بعد أول تحقق بالبريد، أنشئ كلمة مرور لتدخل بها لاحقًا دون طلب رمز في كل مرة. لا نخزن كلمة المرور في المتصفح.' : 'After your first email verification, create a password for later sign-ins without requesting a code each time. The browser does not store it.'}</p>
          <form className="auth-form" onSubmit={savePassword}>
            {passwordConfigured && !passwordResetAllowed ? (
              <label className="field-label"><span>{ar ? 'كلمة المرور الحالية' : 'Current password'}</span>
                <input autoComplete="current-password" minLength={12} onChange={(event) => setCurrentPassword(event.target.value)} required type="password" value={currentPassword} />
              </label>
            ) : null}
            <label className="field-label"><span>{ar ? 'كلمة المرور الجديدة' : 'New password'}</span>
              <input autoComplete="new-password" minLength={12} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
            </label>
            <label className="field-label"><span>{ar ? 'تأكيد كلمة المرور الجديدة' : 'Confirm new password'}</span>
              <input autoComplete="new-password" minLength={12} onChange={(event) => setConfirmation(event.target.value)} required type="password" value={confirmation} />
            </label>
            <p>{passwordResetAllowed
              ? (ar ? 'تحققت من بريدك مؤخرًا؛ يمكنك إنشاء كلمة المرور أو إعادة تعيينها الآن دون القديمة. تنتهي هذه المهلة بعد 10 دقائق.' : 'You recently verified your email; you may create or reset the password without the old one for ten minutes.')
              : (ar ? '12 إلى 128 حرفًا، مع حرف كبير وصغير ورقم ورمز.' : '12–128 characters with uppercase and lowercase letters, a number, and a symbol.')}</p>
            {error ? <p className="form-error" role="alert">{error}</p> : null}
            {message ? <p className="form-success" role="status">{message}</p> : null}
            <button className="button button-primary" disabled={submitting} type="submit">{submitting ? (ar ? 'جارٍ الحفظ…' : 'Saving…') : (ar ? 'حفظ كلمة المرور' : 'Save password')}</button>
          </form>
        </section>

        <section className="account-section">
          <h2>{ar ? 'إنهاء الجلسة' : 'End session'}</h2>
          <button className="button button-secondary" onClick={logOut} type="button">{ar ? 'تسجيل الخروج' : 'Sign out'}</button>
        </section>
      </section>
    </AppShell>
  );
}
