import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import { useLanguage } from '../i18n';

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const submit = (event) => {
    event.preventDefault();

    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError(ar ? 'أدخل بريدًا إلكترونيًا صالحًا.' : 'Enter a valid email address.');
      return;
    }

    navigate(`/reset-password?email=${encodeURIComponent(email)}`);
  };

  return (
    <AuthLayout
      description={
        ar
          ? 'ابدأ تجربة استعادة كلمة المرور. لا يتم إرسال بريد فعلي.'
          : 'Start the password-recovery preview. No real email is sent.'
      }
      eyebrow={ar ? 'استعادة الوصول' : 'Account recovery'}
      title={ar ? 'نسيت كلمة المرور؟' : 'Forgot your password?'}
    >
      <form className="auth-form" onSubmit={submit}>
        <label className="field-label">
          <span>{ar ? 'البريد المهني' : 'Work email'}</span>
          <input
            className="technical-input"
            dir="ltr"
            onChange={(event) => {
              setEmail(event.target.value);
              setError('');
            }}
            type="email"
            value={email}
          />
        </label>

        {error ? <p className="form-error" role="alert">{error}</p> : null}

        <button className="button button-primary button-wide" type="submit">
          {ar ? 'متابعة إلى التحقق' : 'Continue to verification'}
        </button>

        <button
          className="button button-ghost button-wide"
          onClick={() => navigate('/login')}
          type="button"
        >
          {ar ? 'العودة لتسجيل الدخول' : 'Back to sign in'}
        </button>
      </form>
    </AuthLayout>
  );
}
