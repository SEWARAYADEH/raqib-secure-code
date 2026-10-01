import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import logo from '../assets/raqib-logo.png';
import { useLanguage } from '../i18n';
import Icon from './Icon';

export default function PublicHeader() {
  const navigate = useNavigate();
  const { language, t, toggleLanguage } = useLanguage();
  const ar = language === 'ar';
  const [menuOpen, setMenuOpen] = useState(false);

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

      <nav aria-label={ar ? 'التنقل العام' : 'Public navigation'} className={`public-links${menuOpen ? ' open' : ''}`} id="public-navigation">
        {links.map((item) => (
          <NavLink
            className={({ isActive }) => (isActive ? 'active' : '')}
            end={item.end}
            key={item.to}
            onClick={() => setMenuOpen(false)}
            to={item.to}
          >
            {item.label}
          </NavLink>
        ))}
        <NavLink className="public-mobile-link" onClick={() => setMenuOpen(false)} to="/login">
          {ar ? 'تسجيل الدخول' : 'Sign in'}
        </NavLink>
        <NavLink className="public-mobile-link public-mobile-cta" onClick={() => setMenuOpen(false)} to="/login?mode=code">
          {ar ? 'ابدأ تحليلًا آمنًا' : 'Start secure analysis'}
        </NavLink>
      </nav>

      <div className="public-actions">
        <button className="button button-ghost compact-button" onClick={toggleLanguage} type="button">
          <Icon name="language" size={17} />
          {t('language')}
        </button>
        <button className="button button-secondary compact-button" onClick={() => navigate('/login')} type="button">
          {ar ? 'تسجيل الدخول' : 'Sign in'}
        </button>
        <button className="button button-primary compact-button" onClick={() => navigate('/login?mode=code')} type="button">
          {ar ? 'ابدأ تحليلًا آمنًا' : 'Start secure analysis'}
        </button>
        <button
          aria-controls="public-navigation"
          aria-expanded={menuOpen}
          aria-label={ar ? 'فتح أو إغلاق قائمة التنقل' : 'Toggle navigation'}
          className="public-menu-button icon-button"
          onClick={() => setMenuOpen((open) => !open)}
          type="button"
        >
          <Icon name={menuOpen ? 'close' : 'menu'} />
        </button>
      </div>
    </header>
  );
}
