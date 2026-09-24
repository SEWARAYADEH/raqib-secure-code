import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import Icon from '../components/Icon';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { beginSignIn, pendingEmail } = useAuth();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [email, setEmail] = useState(pendingEmail || '');
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError('');

    if (!email.trim()) {
      setError(ar ? 'أدخل البريد الإلكتروني.' : 'Enter your email address.');
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError(ar ? 'أدخل بريدًا إلكترونيًا صالحًا.' : 'Enter a valid email address.');
      return;
    }

    try {
      setSubmitting(true);
      const result = await beginSignIn(email, { remember });
      if (result.requiresTwoFactor) {
        navigate('/two-factor', { state: { from: location.state?.from ?? '/projects' } });
        return;
      }
    } catch (requestError) {
      setError(
        requestError.code === 'EMAIL_DELIVERY_UNAVAILABLE'
          ? (ar ? 'إرسال البريد غير مهيأ بعد. يلزم ضبط بيانات SMTP على الخادم.' : 'Email delivery is not configured. Set the server SMTP credentials.')
          : requestError.code === 'UNTRUSTED_REQUEST_ORIGIN'
            ? (ar ? 'عنوان الموقع غير مسموح به في إعدادات الخادم.' : 'This site origin is not allowed by the server.')
            : requestError.code === 'CHALLENGE_REJECTED'
              ? (ar ? 'انتظر دقيقة قبل طلب رمز جديد.' : 'Wait one minute before requesting another code.')
              : (ar ? 'تعذر إرسال رمز التحقق. حاول مرة أخرى لاحقًا.' : 'The verification code could not be sent. Try again later.'),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      description={ar ? 'سنرسل رمزًا قصير العمر إلى البريد المسموح به.' : 'We will send a short-lived code to the allowed email address.'}
      eyebrow={ar ? 'هوية المستخدم' : 'Identity'}
      title={ar ? 'تسجيل الدخول' : 'Sign in'}
    >
      <form className="auth-form" onSubmit={submit}>
        <label className="field-label">
          <span>{ar ? 'البريد المهني' : 'Work email'}</span>
          <input
            autoComplete="email"
            className="technical-input"
            dir="ltr"
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            value={email}
          />
        </label>

        <div className="auth-form-row">
          <label className="check-control">
            <input checked={remember} onChange={(event) => setRemember(event.target.checked)} type="checkbox" />
            <span>{ar ? 'تذكر هذا الجهاز' : 'Remember this device'}</span>
          </label>
          <button className="text-link" onClick={() => navigate('/forgot-password')} type="button">
            {ar ? 'نسيت كلمة المرور؟' : 'Forgot password?'}
          </button>
        </div>

        {error ? <p className="form-error" role="alert">{error}</p> : null}

        <button className="button button-primary button-wide" disabled={submitting} type="submit">
          {submitting ? (ar ? 'جارٍ إرسال الرمز…' : 'Sending code…') : (ar ? 'إرسال رمز التحقق' : 'Send verification code')}
        </button>

        <p className="auth-switch">
          {ar ? 'ليس لديك حساب؟' : 'New to Raqeeb?'}{' '}
          <button className="text-link" onClick={() => navigate('/create-account')} type="button">
            {ar ? 'إنشاء حساب' : 'Create account'}
          </button>
        </p>
      </form>

      <aside className="demo-boundary">
        <Icon name="info" size={17} />
        <span>
          {ar
            ? 'الرمز يُولّد ويُتحقق منه في الخادم، ولا يُعرض أو يُخزن كنص صريح في الواجهة.'
            : 'The server generates and verifies the code; the frontend never displays or stores its plaintext value.'}
        </span>
      </aside>
    </AuthLayout>
  );
}
