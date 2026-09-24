import PublicHeader from '../components/PublicHeader';
import { useLanguage } from '../i18n';

export default function SecurityTrustPage() {
  const { direction, language } = useLanguage();
  const ar = language === 'ar';

  const sections = ar
    ? [
        [
          'التعامل مع الكود',
          'يستقبل Backend ملف كود واحدًا أو ZIP ضمن حدود صارمة، ويحلل المحتوى ساكنًا داخل مساحة مؤقتة دون تشغيله. تُحذف مساحة ZIP بعد انتهاء التحليل.',
        ],
        [
          'دور AI',
          'AI مصمم للمساعدة في الفهم والربط واقتراح Secure Candidate، وليس كدليل مطلق على أن الكود آمن.',
        ],
        [
          'التحقق',
          'النتيجة الحالية Observation أو Evidence Path فقط. لا توجد حالة Verified Remediated حتى تُنفذ مراحل Test وReplay وRe-Scan وRe-Trace.',
        ],
        [
          'تحكم المطور',
          'يبقى الملف والدالة والسطر والسبب الجذري والـdiff ظاهرًا للمطور قبل تنزيل النسخة المعدّلة.',
        ],
      ]
    : [
        [
          'Code handling',
          'The backend accepts one source file or a tightly bounded ZIP, performs non-executing static analysis in a temporary workspace, and removes ZIP workspaces after analysis.',
        ],
        [
          'AI role',
          'AI is intended to assist understanding, correlation, and secure-candidate generation. It does not prove that code is secure.',
        ],
        [
          'Verification',
          'Current results are observations or evidence paths only. Verified Remediated is unavailable until Test, Replay, Re-Scan, and Re-Trace are implemented.',
        ],
        [
          'Developer control',
          'Developers can inspect file, function, line, root cause, and code diff before downloading the updated artifact.',
        ],
      ];

  return (
    <div className={`public-site ${ar ? 'font-ar' : ''}`} dir={direction}>
      <PublicHeader />
      <main className="public-content-page">
        <header className="public-page-heading">
          <span className="eyebrow">SECURITY & TRUST</span>
          <h1>
            {ar
              ? 'الثقة تبدأ من حدود واضحة، لا من ادعاءات كبيرة.'
              : 'Trust starts with explicit boundaries, not big claims.'}
          </h1>
          <p>
            {ar
              ? 'منتج الأمن يجب ألا يعتمد على ادعاءات غير مدعومة. الموقع يوضح ما ينفذه المحرك الآن وما بقي خارج نطاق الإثبات.'
              : 'A security product should not rely on unsupported claims. The site states what the engine performs now and what remains outside the verified boundary.'}
          </p>
        </header>

        <section className="trust-list">
          {sections.map(([title, text]) => (
            <article key={title}>
              <h2>{title}</h2>
              <p>{text}</p>
            </article>
          ))}
        </section>

        <section className="trust-boundary">
          <span className="eyebrow">CURRENT BOUNDARY</span>
          <p>
            {ar
              ? 'المتوفر الآن: تحليل ساكن متعدد اللغات لبايثون وجافاسكربت، تتبع داخل الدالة وبين دالتين محليتين، ZIP آمن، وعقد API. غير المتوفر: إثبات استغلال، إصلاح آلي، بريد وTOTP وSession Server وAI API.'
              : 'Available now: Python and JavaScript static analysis, intra-function and one-boundary local tracing, secure ZIP intake, and a versioned API. Not available: exploit proof, automated remediation, email, TOTP, session server, or AI API.'}
          </p>
        </section>
      </main>
    </div>
  );
}
