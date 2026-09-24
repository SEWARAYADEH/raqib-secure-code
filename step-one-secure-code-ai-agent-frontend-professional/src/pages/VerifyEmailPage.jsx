import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import OtpInput from '../components/OtpInput';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';

const DEMO_CODE = '482169';

export default function VerifyEmailPage() {
  const navigate = useNavigate();
  const { pendingEmail, verifyEmail } = useAuth();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [code, setCode] = useState('');
  const [seconds, setSeconds] = useState(45);
  const [attempts, setAttempts] = useState(0);
  const [state, setState] = useState('idle');
  const locked = attempts >= 3;

  useEffect(() => {
    if (seconds <= 0) return undefined;

    const timer = window.setInterval(() => {
      setSeconds((value) => Math.max(value - 1, 0));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [seconds]);

  const submit = (event) => {
    event.preventDefault();
    if (locked || code.length !== 6) return;

    if (code !== DEMO_CODE) {
      setAttempts((value) => value + 1);
      setState('invalid');
      return;
    }

    verifyEmail();
    setState('success');
    window.setTimeout(() => navigate('/login'), 450);
  };

  const resend = () => {
    if (seconds > 0 || locked) return;
    setSeconds(45);
    setState('resent');
    setCode('');
  };

  return (
    <AuthLayout
      description={
        ar
          ? 'أدخل رمز التحقق لإكمال تجربة إنشاء الحساب.'
          : 'Enter the verification code to complete the account preview.'
      }
      eyebrow={ar ? 'التحقق من البريد' : 'Email verification'}
      title={ar ? 'تحقق من بريدك' : 'Verify your email'}
    >
      <div className="verification-address">
        <span>{ar ? 'البريد' : 'Email'}</span>
        <strong dir="ltr">{pendingEmail || 'engineer@example.com'}</strong>
        <button
          className="text-link"
          onClick={() => navigate('/create-account')}
          type="button"
        >
          {ar ? 'تغيير البريد' : 'Change email'}
        </button>
      </div>

      <form className="auth-form" onSubmit={submit}>
        <OtpInput
          ariaLabel={ar ? 'رمز التحقق' : 'Verification code'}
          disabled={locked}
          onChange={(value) => {
            setCode(value);
            setState('idle');
          }}
          value={code}
        />

        <p className="demo-code-note">
          {ar ? 'رمز العرض في Frontend:' : 'Frontend demo code:'}{' '}
          <code>{DEMO_CODE}</code>
        </p>

        {state === 'invalid' ? (
          <p className="form-error" role="alert">
            {ar ? 'الرمز غير صحيح.' : 'The code is invalid.'}
          </p>
        ) : null}

        {state === 'resent' ? (
          <p className="form-success" role="status">
            {ar
              ? 'تمت إعادة ضبط حالة العرض. لم يُرسل بريد فعلي.'
              : 'Preview state reset. No real email was sent.'}
          </p>
        ) : null}

        {state === 'success' ? (
          <p className="form-success" role="status">
            {ar
              ? 'تم التحقق في حالة Frontend التجريبية.'
              : 'Verified in the frontend demo state.'}
          </p>
        ) : null}

        {locked ? (
          <p className="form-error" role="alert">
            {ar
              ? 'تم إيقاف المحاولات في العرض بعد 3 محاولات.'
              : 'Preview attempts locked after 3 failures.'}
          </p>
        ) : null}

        <button
          className="button button-primary button-wide"
          disabled={locked || code.length !== 6 || state === 'success'}
          type="submit"
        >
          {ar ? 'تحقق' : 'Verify'}
        </button>

        <button
          className="button button-ghost button-wide"
          disabled={seconds > 0 || locked}
          onClick={resend}
          type="button"
        >
          {seconds > 0
            ? (ar ? `إعادة الإرسال بعد ${seconds}ث` : `Resend in ${seconds}s`)
            : (ar ? 'إعادة إرسال الرمز' : 'Resend code')}
        </button>
      </form>

      <p className="auth-footnote">
        {ar
          ? 'لا توجد خدمة بريد في هذه المرحلة؛ هذه حالات UX فقط.'
          : 'There is no email service in this phase; these are UX states only.'}
      </p>
    </AuthLayout>
  );
}
