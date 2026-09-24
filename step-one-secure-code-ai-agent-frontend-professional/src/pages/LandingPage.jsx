import { useNavigate } from 'react-router-dom';
import PublicHeader from '../components/PublicHeader';
import StatusBadge from '../components/StatusBadge';
import { useLanguage } from '../i18n';

export default function LandingPage() {
  const navigate = useNavigate();
  const { direction, language } = useLanguage();
  const ar = language === 'ar';

  const workflow = ar
    ? [
        ['01', 'افهم', 'حدد اللغة، وظيفة الملف، والدوال المؤثرة.'],
        ['02', 'حلّل', 'اربط المدخلات والمسارات بالسياق الحقيقي للكود.'],
        ['03', 'ارصد', 'اعرض Source وSink والمسار كدليل دون ادعاء ثغرة.'],
        ['04', 'أصلح', 'اعرض Secure Candidate كفرق واضح في الكود.'],
        ['05', 'تحقق', 'أعد الفحص قبل اعتبار المعالجة مثبتة.'],
        ['06', 'وثّق', 'اجمع النتيجة والإصلاح والدليل في تقرير هندسي.'],
      ]
    : [
        ['01', 'Understand', 'Identify language, file purpose, and relevant functions.'],
        ['02', 'Analyze', 'Connect input and execution paths to real code context.'],
        ['03', 'Observe', 'Show source, sink, and path evidence without declaring a vulnerability.'],
        ['04', 'Repair', 'Present a secure candidate as a reviewable code diff.'],
        ['05', 'Verify', 'Re-check before treating remediation as proven.'],
        ['06', 'Report', 'Keep the finding, change, and evidence in one engineering record.'],
      ];

  return (
    <div className={`public-site ${ar ? 'font-ar' : ''}`} dir={direction}>
      <PublicHeader />

      <main>
        <section className="product-hero">
          <div className="product-hero-copy">
            <span className="eyebrow">SECURE CODE ENGINEERING</span>
            <h1>
              {ar
                ? 'افهم الكود الضعيف. ابنِ النسخة الآمنة. ثم أثبت التغيير.'
                : 'Understand vulnerable code. Build the secure version. Verify the change.'}
            </h1>
            <p>
              {ar
                ? 'رقيب مساحة عمل أمنية للمطور تربط كل Finding بالملف والدالة والسطر، ثم تعرض الإصلاح المقترح ونتيجة التحقق بجانب الكود نفسه.'
                : 'Raqeeb is a developer-security workbench that ties each finding to a file, function, and line, then keeps remediation and verification beside the code.'}
            </p>
            <div className="hero-actions">
              <button className="button button-primary button-large" onClick={() => navigate('/create-account')} type="button">
                {ar ? 'ابدأ تحليلًا آمنًا' : 'Start secure analysis'}
              </button>
              <button className="button button-ghost button-large" onClick={() => navigate('/how-it-works')} type="button">
                {ar ? 'شاهد طريقة العمل' : 'See how it works'}
              </button>
            </div>
            <p className="hero-disclaimer">
              {ar
                ? 'تحليل الملفات وZIP يعمل الآن عبر Backend ساكن لا ينفذ الكود. إثبات الاستغلال والإصلاح والتحقق النهائي مراحل لاحقة.'
                : 'File and ZIP analysis now use a non-executing static backend. Exploit verification, remediation, and final closure remain later stages.'}
            </p>
          </div>

          <section className="product-preview" aria-label={ar ? 'تصور مساحة العمل المستقبلية' : 'Future secure workbench illustration'} dir="ltr">
            <header className="preview-header">
              <div>
                <span>ILLUSTRATIVE WORKBENCH · Customer Portal</span>
                <strong>app/routes/users.py</strong>
              </div>
              <StatusBadge tone="danger">Critical</StatusBadge>
            </header>
            <div className="preview-layout">
              <aside className="preview-files">
                <span className="preview-label">FILES</span>
                <div className="active">users.py <b>1</b></div>
                <div>user_service.py <b>1</b></div>
                <div>validators.py <b>✓</b></div>
              </aside>
              <div className="preview-code">
                <span className="preview-label">CODE EVIDENCE</span>
                <pre>{`09  @login_required\n10  def get_user(user_id):\n11    user = service.get_user(user_id)\n12    return jsonify(user.to_dict())`}</pre>
                <div className="preview-diff">
                  <span>- service.get_user(user_id)</span>
                  <strong>+ service.get_user_for_principal(...)</strong>
                </div>
              </div>
              <aside className="preview-finding">
                <span className="preview-label">FINDING</span>
                <strong>Missing object-level authorization</strong>
                <dl>
                  <div><dt>Reference</dt><dd>CWE-639</dd></div>
                  <div><dt>Line</dt><dd>11</dd></div>
                  <div><dt>State</dt><dd>Verification required</dd></div>
                </dl>
              </aside>
            </div>
          </section>
        </section>

        <section className="public-section workflow-section">
          <div className="section-heading">
            <span className="eyebrow">WORKFLOW</span>
            <h2>{ar ? 'مسار واحد من الكود إلى الدليل.' : 'One workflow from code to evidence.'}</h2>
            <p>
              {ar
                ? 'لا ننقل المستخدم بين Widgets لا علاقة لها ببعضها. كل خطوة تبني على السابقة.'
                : 'No unrelated dashboard widgets. Every step builds directly on the one before it.'}
            </p>
          </div>
          <div className="workflow-list">
            {workflow.map(([index, title, text]) => (
              <article className="workflow-item" key={index}>
                <span>{index}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="public-section public-callout">
          <div>
            <span className="eyebrow">SECURITY & TRUST</span>
            <h2>{ar ? 'الـAI يقترح. الدليل هو الذي يثبت.' : 'AI proposes. Evidence proves.'}</h2>
            <p>
              {ar
                ? 'رقيب يفصل بصريًا بين اقتراح الإصلاح وحالة التحقق حتى لا يتحول اقتراح AI إلى ادعاء أمني.'
                : 'Raqeeb visually separates a proposed fix from verified remediation so an AI suggestion is never presented as security proof.'}
            </p>
          </div>
          <button className="button button-secondary" onClick={() => navigate('/security-trust')} type="button">
            {ar ? 'اقرأ نموذج الثقة' : 'Read the trust model'}
          </button>
        </section>
      </main>
    </div>
  );
}
