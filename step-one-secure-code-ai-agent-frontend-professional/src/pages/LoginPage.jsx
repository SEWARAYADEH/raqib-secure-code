import { useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import Icon from '../components/Icon';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { beginSignIn, pendingEmail, signInWithPassword } = useAuth();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [email, setEmail] = useState(pendingEmail || '');
  const [mode, setMode] = useState(searchParams.get('mode') === 'code' ? 'code' : 'password');
  const [password, setPassword] = useState('');
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
      if (mode === 'password') {
        await signInWithPassword(email, password);
        setPassword('');
        navigate(location.state?.from ?? '/projects', { replace: true });
      } else {
        const result = await beginSignIn(email);
        if (result.requiresTwoFactor) {
          navigate('/two-factor', { state: { from: location.state?.from ?? '/account' } });
        }
      }
    } catch (requestError) {
      setError(
        requestError.code === 'PASSWORD_AUTH_FAILED'
          ? (ar ? 'البريد أو كلمة المرور غير صحيحة، أو الدخول متوقف مؤقتًا بعد محاولات متكررة.' : 'Email or password is incorrect, or sign-in is temporarily limited after repeated attempts.')
          : requestError.code === 'EMAIL_DELIVERY_UNAVAILABLE'
          ? (ar ? 'تعذّر إرسال رمز التحقق عبر خادم البريد. تحقّق من إعدادات SMTP واعتماد صندوق البريد.' : 'The mail server could not send the verification code. Check SMTP settings and mailbox credentials.')
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
      description={ar ? 'ادخل بكلمة المرور بعد توثيق بريدك مرة واحدة، أو اختر رمز البريد للدخول الأول.' : 'Use your password after verifying email once, or choose an email code for your first sign-in.'}
      eyebrow={ar ? 'هوية المستخدم' : 'Identity'}
      title={ar ? 'تسجيل الدخول' : 'Sign in'}
    >
      <div className="segmented-control" role="group" aria-label={ar ? 'طريقة الدخول' : 'Sign-in method'}>
        <button className={mode === 'password' ? 'active' : ''} onClick={() => { setMode('password'); setError(''); }} type="button">{ar ? 'كلمة المرور' : 'Password'}</button>
        <button className={mode === 'code' ? 'active' : ''} onClick={() => { setMode('code'); setError(''); }} type="button">{ar ? 'رمز البريد' : 'Email code'}</button>
      </div>
      <form className="auth-form" onSubmit={submit}>
        <label className="field-label" htmlFor="login-email">
          <span>{ar ? 'البريد الإلكتروني' : 'Email address'}</span>
          <input
            autoComplete="email"
            className="technical-input"
            dir="ltr"
            id="login-email"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="name@example.com"
            required
            type="email"
            value={email}
          />
        </label>
        {mode === 'password' ? (
          <label className="field-label" htmlFor="login-password">
            <span>{ar ? 'كلمة المرور' : 'Password'}</span>
            <input autoComplete="current-password" id="login-password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </label>
        ) : null}

        <p className="auth-footnote">{mode === 'password'
          ? (ar ? 'لم تنشئ كلمة مرور بعد؟ اختر «رمز البريد»، ثم أنشئها من الحساب والأمان بعد الدخول. تبقى الجلسة صالحة حتى سبعة أيام.' : 'No password yet? Choose Email code, then create one in Account and security. Your session lasts up to seven days.')
          : (ar ? 'سنرسل رمزًا واحدًا صالحًا لعشر دقائق إلى البريد المسموح به. يلزم أن يكون SMTP يعمل.' : 'We will send a single-use code valid for ten minutes. SMTP delivery must be working.')}</p>
        {mode === 'password' ? <Link className="auth-recovery-link" to="/login?mode=code" onClick={() => setMode('code')}>{ar ? 'نسيت كلمة المرور؟ تحقق بالبريد لإعادة تعيينها' : 'Forgot password? Verify email to reset it'}</Link> : null}

        {error ? <p className="form-error" role="alert">{error}</p> : null}

        <button className="button button-primary button-wide" disabled={submitting} type="submit">
          {submitting ? (ar ? 'جارٍ المتابعة…' : 'Please wait…') : mode === 'password' ? (ar ? 'تسجيل الدخول' : 'Sign in') : (ar ? 'إرسال رمز التحقق' : 'Send verification code')}
        </button>
      </form>

      <aside className="demo-boundary">
        <Icon name="info" size={17} />
        <span>
          {ar
            ? 'كلمة المرور تُتحقق على الخادم وتُخزن كـ hash؛ لا تُحفظ في واجهة المتصفح. رمز البريد يتيح إعدادها أول مرة.'
            : 'The server verifies a hashed password; the browser does not store it. Email verification enables initial setup.'}
        </span>
      </aside>
    </AuthLayout>
  );
}
