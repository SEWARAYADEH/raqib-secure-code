import { useNavigate } from 'react-router-dom';
import logo from '../assets/raqib-logo.png';
import { useLanguage } from '../i18n';
import Icon from './Icon';

export default function AuthLayout({ children, eyebrow, title, description }) {
  const navigate = useNavigate();
  const { direction, language, t, toggleLanguage } = useLanguage();
  const ar = language === 'ar';

  return (
    <main className={`auth-shell ${ar ? 'font-ar' : ''}`} dir={direction}>
      <section className="auth-context">
        <button className="auth-brand" onClick={() => navigate('/')} type="button">
          <img alt="Raqeeb SecClosure" src={logo} />
          <span>
            <strong>رقيب</strong>
            <small>SecClosure</small>
          </span>
        </button>
        <div className="auth-context-copy">
          <span className="eyebrow">SECURE CODE WORKFLOW</span>
          <h1>{ar ? 'الكود أولًا. الدليل ثانيًا.' : 'Code first. Evidence next.'}</h1>
          <p>
            {ar
              ? 'بيئة عمل للمطور تربط النتيجة الأمنية بالسطر، والدالة، والإصلاح، ثم التحقق.'
              : 'A developer workbench that ties security findings to code, remediation, and verification.'}
          </p>
          <div className="auth-flow" dir="ltr">
            <span>Code</span><b>→</b><span>Finding</span><b>→</b><span>Fix</span><b>→</b><span>Verify</span>
          </div>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel-topline">
          <button className="text-link" onClick={() => navigate('/')} type="button">
            <Icon name="arrowBack" size={17} />
            {ar ? 'الرئيسية' : 'Home'}
          </button>
          <button className="icon-button text-button" onClick={toggleLanguage} type="button">
            <Icon name="language" size={17} />
            {t('language')}
          </button>
        </div>

        <div className="auth-panel-heading">
          {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>

        {children}
      </section>
    </main>
  );
}
