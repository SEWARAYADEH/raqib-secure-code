import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import Icon from '../components/Icon';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';

function passwordChecks(password) {
  return {
    length: password.length >= 10,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    symbol: /[^A-Za-z0-9]/.test(password),
  };
}

export default function CreateAccountPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { language } = useLanguage();
  const ar = language === 'ar';
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirm: '',
    terms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const checks = useMemo(() => passwordChecks(form.password), [form.password]);
  const strongEnough = Object.values(checks).every(Boolean);

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const submit = (event) => {
    event.preventDefault();
    setError('');

    if (!form.fullName.trim() || !form.email.trim() || !form.password || !form.confirm) {
      setError(ar ? 'أكمل جميع الحقول المطلوبة.' : 'Complete all required fields.');
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(form.email)) {
      setError(ar ? 'أدخل بريدًا إلكترونيًا صالحًا.' : 'Enter a valid email address.');
      return;
    }

    if (!strongEnough) {
      setError(
        ar
          ? 'كلمة المرور لا تحقق المتطلبات الموضحة.'
          : 'Password does not meet the requirements below.',
      );
      return;
    }

    if (form.password !== form.confirm) {
      setError(ar ? 'كلمتا المرور غير متطابقتين.' : 'Passwords do not match.');
      return;
    }

    if (!form.terms) {
      setError(
        ar
          ? 'وافق على إقرار الاستخدام للمتابعة.'
          : 'Acknowledge the usage terms to continue.',
      );
      return;
    }

    setSubmitting(true);
    window.setTimeout(() => {
      register({ fullName: form.fullName, email: form.email });
      setSubmitting(false);
      navigate('/verify-email');
    }, 280);
  };

  const requirements = [
    ['length', ar ? '10 أحرف على الأقل' : 'At least 10 characters'],
    ['upper', ar ? 'حرف إنجليزي كبير' : 'Uppercase letter'],
    ['lower', ar ? 'حرف إنجليزي صغير' : 'Lowercase letter'],
    ['number', ar ? 'رقم' : 'Number'],
    ['symbol', ar ? 'رمز خاص' : 'Special character'],
  ];

  return (
    <AuthLayout
      description={
        ar
          ? 'أنشئ حساب العرض ثم مرّ بتجربة التحقق من البريد.'
          : 'Create a demo account and continue through email verification.'
      }
      eyebrow={ar ? 'حساب جديد' : 'Create account'}
      title={ar ? 'إنشاء حساب رقيب' : 'Create your Raqeeb account'}
    >
      <form className="auth-form" onSubmit={submit}>
        <label className="field-label">
          <span>{ar ? 'الاسم الكامل' : 'Full name'}</span>
          <input
            autoComplete="name"
            onChange={(event) => update('fullName', event.target.value)}
            value={form.fullName}
          />
        </label>

        <label className="field-label">
          <span>{ar ? 'البريد المهني' : 'Work email'}</span>
          <input
            autoComplete="email"
            className="technical-input"
            dir="ltr"
            onChange={(event) => update('email', event.target.value)}
            type="email"
            value={form.email}
          />
        </label>

        <label className="field-label">
          <span>{ar ? 'كلمة المرور' : 'Password'}</span>
          <span className="password-field">
            <input
              autoComplete="new-password"
              dir="ltr"
              onChange={(event) => update('password', event.target.value)}
              type={showPassword ? 'text' : 'password'}
              value={form.password}
            />
            <button
              aria-label={ar ? 'إظهار كلمة المرور' : 'Show password'}
              onClick={() => setShowPassword((value) => !value)}
              type="button"
            >
              <Icon name="eye" size={18} />
            </button>
          </span>
        </label>

        <div className="password-requirements">
          {requirements.map(([key, label]) => (
            <span className={checks[key] ? 'met' : ''} key={key}>
              <Icon name="check" size={14} />
              {label}
            </span>
          ))}
        </div>

        <label className="field-label">
          <span>{ar ? 'تأكيد كلمة المرور' : 'Confirm password'}</span>
          <input
            autoComplete="new-password"
            dir="ltr"
            onChange={(event) => update('confirm', event.target.value)}
            type="password"
            value={form.confirm}
          />
        </label>

        <label className="check-control align-start">
          <input
            checked={form.terms}
            onChange={(event) => update('terms', event.target.checked)}
            type="checkbox"
          />
          <span>
            {ar
              ? 'أقر أن هذه تجربة Frontend وأن إنشاء الحساب الحقيقي يحتاج Backend.'
              : 'I understand this is a frontend preview; real account creation needs a backend.'}
          </span>
        </label>

        {error ? <p className="form-error" role="alert">{error}</p> : null}

        <button
          className="button button-primary button-wide"
          disabled={submitting}
          type="submit"
        >
          {submitting
            ? (ar ? 'تجهيز خطوة التحقق…' : 'Preparing verification…')
            : (ar ? 'إنشاء حساب العرض' : 'Create demo account')}
        </button>

        <p className="auth-switch">
          {ar ? 'لديك حساب بالفعل؟' : 'Already have an account?'}{' '}
          <button
            className="text-link"
            onClick={() => navigate('/login')}
            type="button"
          >
            {ar ? 'تسجيل الدخول' : 'Sign in'}
          </button>
        </p>
      </form>
    </AuthLayout>
  );
}
