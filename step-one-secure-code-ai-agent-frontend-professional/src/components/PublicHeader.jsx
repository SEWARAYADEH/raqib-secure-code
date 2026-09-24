import { NavLink, useNavigate } from 'react-router-dom';
import logo from '../assets/raqib-logo.png';
import { useLanguage } from '../i18n';
import Icon from './Icon';

export default function PublicHeader() {
  const navigate = useNavigate();
  const { language, t, toggleLanguage } = useLanguage();
  const ar = language === 'ar';

  const links = [
    { to: '/', label: ar ? 'الرئيسية' : 'Home', end: true },
    { to: '/how-it-works', label: ar ? 'كيف يعمل' : 'How it works' },
    { to: '/security-trust', label: ar ? 'الأمان والثقة' : 'Security & trust' },
  ];

  return (
    <header className="public-header">
      <button className="public-brand" onClick={() => navigate('/')} type="button">
        <img alt="Raqeeb SecClosure" src={logo} />
        <span>
          <strong>رقيب</strong>
          <small>SecClosure</small>
        </span>
      </button>

      <nav aria-label={ar ? 'التنقل العام' : 'Public navigation'} className="public-links">
        {links.map((item) => (
          <NavLink
            className={({ isActive }) => (isActive ? 'active' : '')}
            end={item.end}
            key={item.to}
            to={item.to}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="public-actions">
        <button className="button button-ghost compact-button" onClick={toggleLanguage} type="button">
          <Icon name="language" size={17} />
          {t('language')}
        </button>
        <button className="button button-secondary compact-button" onClick={() => navigate('/login')} type="button">
          {ar ? 'تسجيل الدخول' : 'Sign in'}
        </button>
        <button className="button button-primary compact-button" onClick={() => navigate('/create-account')} type="button">
          {ar ? 'ابدأ تحليلًا آمنًا' : 'Start secure analysis'}
        </button>
      </div>
    </header>
  );
}
