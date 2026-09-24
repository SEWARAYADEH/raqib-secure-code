import { useNavigate } from 'react-router-dom';
import logo from '../assets/raqib-logo.png';
import Icon from '../components/Icon';
import { useLanguage } from '../i18n';

const copy = {
  unauthorized: {
    code: '401',
    en: ['Sign-in required', 'This area requires an authenticated backend session.'],
    ar: ['تسجيل الدخول مطلوب', 'هذه المنطقة تحتاج جلسة مصادقة حقيقية من الـBackend.'],
  },
  forbidden: {
    code: '403',
    en: ['Access not allowed', 'The backend must decide whether this account can access this resource.'],
    ar: ['الوصول غير مسموح', 'الـBackend هو المسؤول عن قرار الصلاحية لهذا المورد.'],
  },
  notFound: {
    code: '404',
    en: ['Page not found', 'The requested frontend route does not exist.'],
    ar: ['الصفحة غير موجودة', 'مسار الواجهة المطلوب غير موجود.'],
  },
};

export default function SystemStatePage({ type = 'notFound' }) {
  const navigate = useNavigate();
  const { direction, language } = useLanguage();
  const ar = language === 'ar';
  const state = copy[type] ?? copy.notFound;
  const [title, text] = ar ? state.ar : state.en;

  return (
    <main className={`system-state-page ${ar ? 'font-ar' : ''}`} dir={direction}>
      <img alt="Raqeeb" src={logo} />
      <span className="system-state-code">{state.code}</span>
      <h1>{title}</h1>
      <p>{text}</p>
      <button className="button button-primary" onClick={() => navigate('/projects')} type="button">
        <Icon name="arrow" />
        {ar ? 'العودة للمشاريع' : 'Back to projects'}
      </button>
    </main>
  );
}
