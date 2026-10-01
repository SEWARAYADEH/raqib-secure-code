import { useState } from 'react';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
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
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError('');

    if (!email.trim()) {
      setError(ar ? 'أدخل البريد الإلكتروني.' : 'Enter your email address.');
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setError(ar ? 'أدخل بريدًا إلكترونيًا صالحًا.' : 'Enter a valid email address.');
      return;
    }

    try {
      setSubmitting(true);
      if (mode === 'password') {
        await signInWithPassword(email.trim(), password);
        setPassword('');
        navigate(location.state?.from ?? '/projects', { replace: true });
      } else {
        const result = await beginSignIn(email.trim());
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
              : (ar ? 'تعذر تسجيل الدخول الآن. حاول مرة أخرى لاحقًا.' : 'Sign-in is unavailable right now. Try again later.'),
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      description={ar ? 'ادخل بكلمة المرور. لأول استخدام، اختر رمز البريد لإعداد الحساب.' : 'Sign in with your password. For first-time setup, choose an email code.'}
      eyebrow={ar ? 'هوية المستخدم' : 'Identity'}
      title={ar ? 'تسجيل الدخول' : 'Sign in'}
    >
      <div className="segmented-control" role="group" aria-label={ar ? 'طريقة الدخول' : 'Sign-in method'}>
        <button className={mode === 'password' ? 'active' : ''} onClick={() => { setMode('password'); setError(''); }} type="button">{ar ? 'كلمة المرور' : 'Password'}</button>
        <button className={mode === 'code' ? 'active' : ''} onClick={() => { setMode('code'); setPassword(''); setShowPassword(false); setError(''); }} type="button">{ar ? 'أول استخدام / رمز البريد' : 'First sign-in / Email code'}</button>
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
          <div className="field-label">
            <label htmlFor="login-password">{ar ? 'كلمة المرور' : 'Password'}</label>
            <span className="password-field">
              <input autoComplete="current-password" id="login-password" onChange={(event) => setPassword(event.target.value)} required type={showPassword ? 'text' : 'password'} value={password} />
              <button aria-label={showPassword ? (ar ? 'إخفاء كلمة المرور' : 'Hide password') : (ar ? 'إظهار كلمة المرور' : 'Show password')} aria-pressed={showPassword} onClick={() => setShowPassword((visible) => !visible)} type="button">{showPassword ? (ar ? 'إخفاء' : 'Hide') : (ar ? 'إظهار' : 'Show')}</button>
            </span>
          </div>
        ) : null}

        <p className="auth-footnote">{mode === 'password'
          ? (ar ? 'بعد توثيق البريد مرة واحدة، اضبط كلمة المرور من الحساب والأمان.' : 'After verifying your email once, set a password in Account and security.')
          : (ar ? 'سنرسل رمزًا صالحًا لعشر دقائق إلى بريدك.' : 'We will email a code valid for ten minutes.')}</p>
        {mode === 'password' ? <Link className="auth-recovery-link" to="/login?mode=code" onClick={() => { setMode('code'); setPassword(''); setShowPassword(false); }}>{ar ? 'نسيت كلمة المرور؟ تحقق بالبريد لإعادة تعيينها' : 'Forgot password? Verify email to reset it'}</Link> : null}

        {error ? <p className="form-error" role="alert">{error}</p> : null}

        <button className="button button-primary button-wide" disabled={submitting} type="submit">
          {submitting ? (ar ? 'جارٍ المتابعة…' : 'Please wait…') : mode === 'password' ? (ar ? 'تسجيل الدخول' : 'Sign in') : (ar ? 'إرسال رمز التحقق' : 'Send verification code')}
        </button>
      </form>

    </AuthLayout>
  );
}
