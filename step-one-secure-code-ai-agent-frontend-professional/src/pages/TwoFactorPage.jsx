import { useState } from 'react';
import { Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import OtpInput from '../components/OtpInput';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';

export default function TwoFactorPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const setupMode = searchParams.get('mode') === 'setup';
  const { challengeId, completeTwoFactor, isAuthenticated, pendingEmail } = useAuth();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (setupMode) {
    return isAuthenticated
      ? <Navigate replace to="/account?tab=security" />
      : <Navigate replace to="/login" />;
  }

  if (!pendingEmail || !challengeId) {
    return <Navigate replace to="/login" />;
  }

  const verify = async (event) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      await completeTwoFactor(code);
      navigate(location.state?.from ?? '/projects', { replace: true });
    } catch {
      setError(ar ? 'الرمز غير صحيح أو منتهي الصلاحية.' : 'The code is invalid or expired.');
      setCode('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      description={ar ? 'أدخل الرمز المرسل إلى بريدك. تنتهي صلاحيته خلال عشر دقائق.' : 'Enter the code sent to your email. It expires in ten minutes.'}
      eyebrow="EMAIL VERIFICATION"
      title={ar ? 'تحقق من البريد' : 'Verify your email'}
    >
      <div className="verification-address">
        <span>{ar ? 'أُرسل إلى' : 'Sent to'}</span>
        <strong dir="ltr">{pendingEmail}</strong>
      </div>

      <form className="auth-form" onSubmit={verify}>
        <OtpInput
          ariaLabel={ar ? 'رمز التحقق' : 'Verification code'}
          disabled={submitting}
          onChange={(value) => {
            setCode(value);
            setError('');
          }}
          value={code}
        />

        {error ? <p className="form-error" role="alert">{error}</p> : null}

        <button className="button button-primary button-wide" disabled={submitting || code.length !== 6} type="submit">
          {submitting ? (ar ? 'جارٍ التحقق…' : 'Verifying…') : (ar ? 'تحقق وادخل' : 'Verify and sign in')}
        </button>
      </form>

      <p className="auth-footnote">
        {ar
          ? 'لا تشارك الرمز. بعد خمس محاولات فاشلة يُلغى التحدي، ويمكن استخدامه مرة واحدة فقط.'
          : 'Do not share the code. The challenge is revoked after five failed attempts and can be used only once.'}
      </p>
    </AuthLayout>
  );
}
