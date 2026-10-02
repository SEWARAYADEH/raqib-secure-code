import { useEffect, useRef, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import logo from '../assets/raqib-logo.png';
import { useAuth } from '../auth';
import { useLanguage } from '../i18n';
import Icon from './Icon';

function projectIdFromPath(pathname) {
  return pathname.match(/^\/projects\/([^/]+)/)?.[1]
    ?? pathname.match(/^\/analysis\/progress\/([^/]+)/)?.[1]
    ?? null;
}

export default function AppShell({ children }) {
  const { language, direction, t, toggleLanguage } = useLanguage();
  const { user, signOut } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [advisorOpen, setAdvisorOpen] = useState(false);
  const advisorDialog = useRef(null);
  const projectId = projectIdFromPath(location.pathname);
  const ar = language === 'ar';

  const baseItems = [
    { key: 'projects', icon: 'projects', to: '/projects', label: ar ? 'المشاريع' : 'Projects' },
    { key: 'newAnalysis', icon: 'scan', to: '/analysis/new', label: ar ? 'تحليل جديد' : 'New analysis' },
  ];

  const projectItems = projectId
    ? [
        { key: 'analysis', icon: 'scan', to: `/analysis/progress/${projectId}`, label: ar ? 'التحليل' : 'Analysis' },
        { key: 'workbench', icon: 'code', to: `/projects/${projectId}/workbench`, label: ar ? 'بنية المشروع' : 'Structure' },
        { key: 'findings', icon: 'findings', to: `/projects/${projectId}/findings`, label: ar ? 'المرشحات' : 'Candidates' },
        { key: 'report', icon: 'report', to: `/projects/${projectId}/report`, label: ar ? 'التقرير' : 'Report' },
      ]
    : [];

  const utilityItems = [
    { key: 'configuration', icon: 'settings', to: '/configuration', label: ar ? 'إعدادات التحليل' : 'Configuration' },
    { key: 'account', icon: 'user', to: '/account', label: ar ? 'الحساب والأمان' : 'Account & security' },
  ];

  const closeMobile = () => setMobileOpen(false);
  const handleSignOut = () => {
    signOut();
    navigate('/login', { replace: true });
  };

  useEffect(() => {
    const dialog = advisorDialog.current;
    if (!dialog) return;
    if (advisorOpen && !dialog.open) dialog.showModal();
    if (!advisorOpen && dialog.open) dialog.close();
  }, [advisorOpen]);

  return (
    <div className={`app-shell ${ar ? 'font-ar' : ''}`} dir={direction}>
      {mobileOpen ? <button aria-label={ar ? 'إغلاق القائمة' : 'Close navigation'} className="sidebar-backdrop" onClick={closeMobile} type="button" /> : null}
      <aside className={`sidebar${mobileOpen ? ' mobile-open' : ''}`}>
        <div className="sidebar-head">
          <button className="brand-block" onClick={() => { navigate('/projects'); closeMobile(); }} type="button">
            <img alt="Raqeeb SecClosure" src={logo} />
            <span>
              <strong>{t('arabicBrand')}</strong>
              <small>{t('brand')}</small>
            </span>
          </button>
          <button className="sidebar-close" onClick={closeMobile} type="button" aria-label={ar ? 'إغلاق القائمة' : 'Close navigation'}>
            <Icon name="close" />
          </button>
        </div>

        <nav aria-label={ar ? 'التنقل الرئيسي' : 'Primary navigation'} className="sidebar-nav">
          <span className="nav-group-label">{ar ? 'المنتج' : 'Product'}</span>
          {baseItems.map((item) => (
            <NavLink className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`} key={item.key} onClick={closeMobile} to={item.to}>
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </NavLink>
          ))}

          {projectItems.length ? (
            <>
              <span className="nav-group-label">{ar ? 'المشروع الحالي' : 'Current project'}</span>
              {projectItems.map((item) => (
                <NavLink className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`} key={item.key} onClick={closeMobile} to={item.to}>
                  <Icon name={item.icon} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </>
          ) : null}

          <span className="nav-group-label">{ar ? 'الإدارة' : 'Manage'}</span>
          {utilityItems.map((item) => (
            <NavLink className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`} key={item.key} onClick={closeMobile} to={item.to}>
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-account">
          <button className="account-summary" onClick={() => { navigate('/account'); closeMobile(); }} type="button">
            <span className="account-avatar">{user?.name?.charAt(0) ?? user?.email?.charAt(0)?.toUpperCase() ?? 'ر'}</span>
            <span>
              <strong>{user?.name ?? (ar ? 'مستخدم موثّق' : 'Verified user')}</strong>
              <small dir="ltr">{user?.email ?? '—'}</small>
            </span>
          </button>
          <button className="signout-button" onClick={handleSignOut} type="button">
            <Icon name="logout" size={17} />
            {ar ? 'تسجيل الخروج' : 'Sign out'}
          </button>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <div className="topbar-leading">
            <button className="mobile-menu-button" onClick={() => setMobileOpen(true)} type="button" aria-label={ar ? 'فتح القائمة' : 'Open navigation'}>
              <Icon name="menu" />
            </button>
            <div className="topbar-title">
              <span className="topbar-dot" />
              <div>
                <strong>{projectId ? (ar ? 'مساحة المشروع' : 'Project workspace') : (ar ? 'رقيب' : 'Raqeeb')}</strong>
                <small>{ar ? 'فهم التطبيق · تتبّع الدليل · حالة واضحة' : 'Application understanding · evidence trace · honest status'}</small>
              </div>
            </div>
          </div>

          <div className="topbar-actions">
            <span className="mock-label">{ar ? 'دليل ساكن' : 'Static evidence'}</span>
            <button aria-controls="advisor-drawer" aria-expanded={advisorOpen} className="icon-button text-button" onClick={() => setAdvisorOpen(true)} type="button"><Icon name="robot" size={17} />{ar ? 'محادثة AI' : 'AI chat'}</button>
            <button className="icon-button text-button" onClick={toggleLanguage} type="button">
              <Icon name="language" size={17} />
              {t('language')}
            </button>
          </div>
        </header>

        <main className="content">{children}</main>
      </div>
      <dialog aria-labelledby="advisor-drawer-title" className="advisor-drawer" id="advisor-drawer" onClose={() => setAdvisorOpen(false)} onClick={(event) => { if (event.target === advisorDialog.current) setAdvisorOpen(false); }} ref={advisorDialog}>
        <div className="advisor-drawer-head"><div><span className="eyebrow">RAQEEB / AI</span><h2 id="advisor-drawer-title">{ar ? 'محادثة AI' : 'AI chat'}</h2></div><button aria-label={ar ? 'إغلاق المحادثة' : 'Close chat'} className="icon-button" onClick={() => setAdvisorOpen(false)} type="button"><Icon name="close" /></button></div>
        <div className="advisor-drawer-body"><span className="candidate-state">NOT AVAILABLE</span><p>{ar ? 'واجهة المحادثة غير متصلة حاليًا بمسار إرسال آمن في الـAPI. لا يُنتج رقيب ردودًا أو إصلاحات بالذكاء الاصطناعي من هذه النافذة.' : 'No secure chat endpoint is available in the current API. This drawer does not generate AI answers or repairs.'}</p><p>{ar ? 'يمكنك مراجعة حالة المفتاح والموديل على الخادم في إعدادات التحليل. تظل أدلة المحرك الساكن هي مصدر حالة النتيجة.' : 'Review server-side key and model status in Configuration. Saved static evidence remains the source of finding status.'}</p><button className="button button-secondary" onClick={() => { setAdvisorOpen(false); navigate('/configuration'); }} type="button">{ar ? 'إعدادات الربط' : 'Connection settings'}</button></div>
      </dialog>
    </div>
  );
}
