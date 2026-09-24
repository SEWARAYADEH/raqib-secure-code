import PublicHeader from '../components/PublicHeader';
import { useLanguage } from '../i18n';

export default function HowItWorksPage() {
  const { direction, language } = useLanguage();
  const ar = language === 'ar';

  const steps = ar
    ? [
        ['01', 'Understand', 'تحديد اللغة والإطار ووظيفة الملفات والدوال ونقاط الدخول.'],
        ['02', 'Analyze', 'ترتيب المسارات والاعتماديات والسياق الذي يغيّر معنى السطر أمنيًا.'],
        ['03', 'Detect', 'إظهار Finding واضحة مع الشدة والموقع والمرجع والدليل المتاح.'],
        ['04', 'Repair', 'تفسير السبب الجذري وعرض Secure Candidate كـdiff قابل للمراجعة.'],
        ['05', 'Verify', 'فصل اقتراح الإصلاح عن التحقق وإظهار حالة إعادة الفحص بوضوح.'],
        ['06', 'Report', 'إخراج سجل تنفيذي وهندسي يوضح ما تغير وما بقي وما تم التحقق منه.'],
      ]
    : [
        ['01', 'Understand', 'Identify language, framework, file purpose, functions, and entry points.'],
        ['02', 'Analyze', 'Organize execution paths, dependencies, and the context that changes security meaning.'],
        ['03', 'Detect', 'Present a clear finding with severity, location, reference, and available evidence.'],
        ['04', 'Repair', 'Explain root cause and show the secure candidate as a reviewable diff.'],
        ['05', 'Verify', 'Separate remediation proposals from verification and re-scan state.'],
        ['06', 'Report', 'Produce an executive and engineering record of changes, remaining risk, and evidence.'],
      ];

  return (
    <div className={`public-site ${ar ? 'font-ar' : ''}`} dir={direction}>
      <PublicHeader />
      <main className="public-content-page">
        <header className="public-page-heading">
          <span className="eyebrow">HOW RAQEEB WORKS</span>
          <h1>{ar ? 'رحلة أمنية واضحة، وليست مجموعة أدوات متفرقة.' : 'A clear security workflow, not a pile of disconnected tools.'}</h1>
          <p>
            {ar
              ? 'القيمة الأساسية هي بقاء الكود والسياق والدليل والإصلاح في تسلسل واحد يفهمه المطور.'
              : 'The core value is keeping code, context, evidence, remediation, and verification in one developer-readable sequence.'}
          </p>
        </header>

        <section className="workflow-detail-list">
          {steps.map(([index, title, text]) => (
            <article key={index}>
              <span className="workflow-detail-index">{index}</span>
              <div>
                <h2 dir="ltr">{title}</h2>
                <p>{text}</p>
              </div>
            </article>
          ))}
        </section>

        <section className="technical-principle" dir={ar ? 'rtl' : 'ltr'}>
          <span className="eyebrow">PRODUCT PRINCIPLE</span>
          <h2>{ar ? 'الكود هو مركز الواجهة.' : 'Code is the center of the interface.'}</h2>
          <p>
            {ar
              ? 'الملف والدالة والسطر لا يختفون خلف لوحات إحصائية. الـFinding، الـCWE، الإصلاح، وحالة التحقق تظهر حول نفس السياق.'
              : 'Files, functions, and lines do not disappear behind analytics. Findings, CWE references, remediation, and verification stay attached to the same context.'}
          </p>
        </section>
      </main>
    </div>
  );
}
