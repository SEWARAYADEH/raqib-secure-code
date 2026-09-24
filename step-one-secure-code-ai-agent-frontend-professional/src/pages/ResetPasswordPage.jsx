import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import OtpInput from '../components/OtpInput';
import { useLanguage } from '../i18n';

const DEMO_CODE = '910426';

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const email = searchParams.get('email') || 'engineer@example.com';
  const [step, setStep] = useState('verify');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');

  const verify = (event) => {
    event.preventDefault();

    if (code !== DEMO_CODE) {
      setError(ar ? 'رمز العرض غير صحيح.' : 'The demo code is invalid.');
      return;
    }

    setError('');
    setStep('password');
  };

  const updatePassword = (event) => {
    event.preventDefault();

    if (password.length < 10) {
      setError(
        ar
          ? 'استخدم كلمة مرور من 10 أحرف على الأقل.'
          : 'Use at least 10 characters.',
      );
      return;
    }

    if (password !== confirm) {
      setError(ar ? 'كلمتا المرور غير متطابقتين.' : 'Passwords do not match.');
      return;
    }

    setError('');
    setStep('done');
  };

  return (
    <AuthLayout
      description={
        ar
          ? 'إكمال تجربة إعادة تعيين كلمة المرور محليًا في الواجهة.'
          : 'Complete the password-reset experience locally in the frontend.'
      }
      eyebrow={ar ? 'إعادة تعيين كلمة المرور' : 'Reset password'}
      title={
        step === 'done'
          ? (ar ? 'تم تحديث حالة العرض' : 'Preview password updated')
          : (ar ? 'استعادة الوصول' : 'Recover access')
      }
    >
      {step === 'verify' ? (
        <form className="auth-form" onSubmit={verify}>
          <div className="verification-address">
            <span>{ar ? 'البريد' : 'Email'}</span>
            <strong dir="ltr">{email}</strong>
          </div>

          <OtpInput
            ariaLabel={ar ? 'رمز الاستعادة' : 'Recovery code'}
            onChange={(value) => {
              setCode(value);
              setError('');
            }}
            value={code}
          />

          <p className="demo-code-note">
            {ar ? 'رمز العرض:' : 'Demo code:'} <code>{DEMO_CODE}</code>
          </p>

          {error ? <p className="form-error" role="alert">{error}</p> : null}

          <button
            className="button button-primary button-wide"
            disabled={code.length !== 6}
            type="submit"
          >
            {ar ? 'تحقق' : 'Verify'}
          </button>
        </form>
      ) : null}

      {step === 'password' ? (
        <form className="auth-form" onSubmit={updatePassword}>
          <label className="field-label">
            <span>{ar ? 'كلمة المرور الجديدة' : 'New password'}</span>
            <input
              autoComplete="new-password"
              dir="ltr"
              onChange={(event) => {
                setPassword(event.target.value);
                setError('');
              }}
              type="password"
              value={password}
            />
          </label>

          <label className="field-label">
            <span>{ar ? 'تأكيد كلمة المرور' : 'Confirm password'}</span>
            <input
              autoComplete="new-password"
              dir="ltr"
              onChange={(event) => {
                setConfirm(event.target.value);
                setError('');
              }}
              type="password"
              value={confirm}
            />
          </label>

          {error ? <p className="form-error" role="alert">{error}</p> : null}

          <button className="button button-primary button-wide" type="submit">
            {ar ? 'تحديث كلمة المرور' : 'Update password'}
          </button>
        </form>
      ) : null}

      {step === 'done' ? (
        <div className="auth-complete">
          <p>
            {ar
              ? 'تم تحديث الحالة محليًا فقط. لم يحدث تغيير في أي Backend.'
              : 'The state changed locally only. No backend password was changed.'}
          </p>
          <button
            className="button button-primary button-wide"
            onClick={() => navigate('/login')}
            type="button"
          >
            {ar ? 'العودة لتسجيل الدخول' : 'Return to sign in'}
          </button>
        </div>
      ) : null}
    </AuthLayout>
  );
}
