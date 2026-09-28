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
          'النتائج الحالية ملاحظات أو مرشحات مدعومة بمسارات ساكنة، وليست ثغرات مؤكدة. لا توجد حالة إغلاق مثبت حتى تُنفذ مراحل Test وReplay وRe-Scan وRe-Trace مع حفظ الدليل.',
        ],
        [
          'تحكم المطور',
          'يمكن مراجعة الملف والدالة والسطر ومسار الدليل في النتيجة المحفوظة. عرض السبب الجذري والـdiff وتنزيل النسخة المعدّلة مؤجل إلى حين وجود إصلاح متحقق منه.',
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
          'Current results are observations or candidates supported by static traces, not confirmed vulnerabilities. Verified closure is unavailable until Test, Replay, Re-Scan, and Re-Trace produce preserved evidence.',
        ],
        [
          'Developer control',
          'Developers can inspect the file, function, line, and evidence path in a saved result. Root cause, code diff, and updated-artifact download await a verified repair.',
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
              ? 'المتوفر الآن: تحليل ساكن لبايثون وجافاسكربت ضمن نطاقات محددة، استقبال ZIP آمن، API، جلسات موقعة، ومسار إرسال رمز بريد قصير العمر. إرسال الرمز الحقيقي متعطل حتى تصح إعدادات SMTP. غير المتوفر: إثبات استغلال، إصلاح آلي، Replay، تنزيل نسخة معدّلة، وTOTP فعلي. مساعد AI اختياري وغير مفعل افتراضيًا.'
              : 'Available now: bounded Python and JavaScript static analysis, secure ZIP intake, an API, signed sessions, and short-lived email-code routes. Real code delivery is blocked until SMTP is configured correctly. Unavailable: exploit proof, automated repair, replay, updated-artifact download, and working TOTP. The AI advisor is optional and disabled by default.'}
          </p>
        </section>
      </main>
    </div>
  );
}
