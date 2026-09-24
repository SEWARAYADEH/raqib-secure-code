import Icon from './Icon';
import StatusBadge from './StatusBadge';
import UpdatedFileDownload from './UpdatedFileDownload';

function severityTone(severity) {
  if (severity === 'Critical') return 'danger';
  if (severity === 'High') return 'warning';
  return 'info';
}

function fileTone(status) {
  if (status === 'critical') return 'danger';
  if (status === 'warning') return 'warning';
  return 'success';
}

function severityLabel(severity, ar) {
  if (!ar) return severity;
  if (severity === 'Critical') return 'حرجة';
  if (severity === 'High') return 'عالية';
  return 'متوسطة';
}

function statusLabel(status, ar) {
  if (!ar) return status;
  if (status === 'critical') return 'حرج';
  if (status === 'warning') return 'مراجعة';
  return 'آمن';
}

function verificationKeyLabel(key, ar) {
  if (!ar) return key;
  const labels = {
    functional: 'الاختبار الوظيفي',
    replay: 'إعادة الاختبار',
    rescan: 'إعادة الفحص',
    retrace: 'إعادة التتبع',
  };
  return labels[key] ?? key;
}

function verificationValueLabel(value, ar) {
  if (!ar) return value;
  const labels = {
    Pass: 'ناجح',
    Pending: 'بانتظار التحقق',
    'Not applicable': 'غير منطبق',
    'Pending environment validation': 'بانتظار التحقق من بيئة التشغيل',
    'Previous cross-account request is denied': 'تم رفض طلب الوصول السابق بين حسابين',
    'Original finding not reproduced': 'لم تعد النتيجة الأصلية قابلة لإعادة الإنتاج',
    'Ownership control appears before resource return': 'ظهر فحص الملكية قبل إرجاع المورد',
  };
  return labels[value] ?? value;
}

export default function WorkbenchInspector({
  ar,
  data,
  file,
  finding,
  onOpenReport,
  onStage,
  selectedFunction,
  workflowId,
}) {
  const workflow = data.workflow.find((item) => item.id === workflowId);
  const workflowLabel = ar ? workflow?.labelAr ?? workflow?.label : workflow?.label;
  const selectedFn = file.functions.find((fn) => fn.name === selectedFunction);

  return (
    <aside className="inspector-pane">
      <div className="pane-heading inspector-heading">
        <div>
          <span className="eyebrow">{ar ? 'التفاصيل' : 'INSPECTOR'}</span>
          <strong>{workflowLabel}</strong>
        </div>
        {finding && ['investigate', 'transform', 'verify'].includes(workflowId) ? (
          <StatusBadge tone={severityTone(finding.severity)}>
            {severityLabel(finding.severity, ar)}
          </StatusBadge>
        ) : null}
      </div>

      <div className="inspector-content">
        {workflowId === 'fingerprint' ? (
          <>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'البصمة التقنية' : 'TECHNOLOGY PROFILE'}</span>
              <h3 className="technical-value">
                {data.technology.language} · {data.technology.framework}
              </h3>
              <p>
                {ar ? 'تطبيق ويب بطبقات واضحة ومكوّنات قابلة للتتبع.' : data.technology.architecture}
              </p>
            </section>
            <section className="inspector-section key-value-grid">
              <div>
                <span>{ar ? 'قاعدة البيانات' : 'Database'}</span>
                <strong className="technical-value">{data.technology.database}</strong>
              </div>
              <div><span>{ar ? 'الملفات' : 'Files'}</span><strong>{data.technology.files}</strong></div>
              <div><span>{ar ? 'الدوال' : 'Functions'}</span><strong>{data.technology.functions}</strong></div>
              <div><span>{ar ? 'المسارات' : 'Routes'}</span><strong>{data.technology.routes}</strong></div>
              <div><span>{ar ? 'الاعتماديات' : 'Dependencies'}</span><strong>{data.technology.dependencies}</strong></div>
            </section>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'المناطق الحساسة' : 'SENSITIVE AREAS'}</span>
              <div className="role-pills technical-pills">
                {data.technology.sensitiveAreas.map((item) => <span key={item}>{item}</span>)}
              </div>
            </section>
            <button
              className="button button-primary button-wide"
              onClick={() => onStage('understand')}
              type="button"
            >
              {ar ? 'التالي: فهم الكود' : 'Next: understand code'}
              <Icon name="arrow" />
            </button>
          </>
        ) : null}

        {workflowId === 'understand' ? (
          <>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'وظيفة العنصر' : 'What does it do?'}</span>
              <h3 className="technical-value">
                {selectedFunction ? `${selectedFunction}()` : file.name}
              </h3>
              <p>
                {selectedFn
                  ? ar ? selectedFn.purposeAr ?? selectedFn.purpose : selectedFn.purpose
                  : ar ? file.purposeAr ?? file.purpose : file.purpose}
              </p>
            </section>
            <section className="inspector-section key-value-grid">
              <div>
                <span>{ar ? 'الملف' : 'File'}</span>
                <strong className="technical-value">{file.name}</strong>
              </div>
              <div>
                <span>{ar ? 'اللغة' : 'Language'}</span>
                <strong className="technical-value">{file.language}</strong>
              </div>
              <div><span>{ar ? 'الدوال' : 'Functions'}</span><strong>{file.functions.length}</strong></div>
              <div><span>{ar ? 'النتائج' : 'Findings'}</span><strong>{file.findings.length}</strong></div>
            </section>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'حالة الدوال' : 'FUNCTION STATUS'}</span>
              {file.functions.length ? file.functions.map((fn) => (
                <div className="verification-row" key={fn.name}>
                  <span className="technical-value">{fn.name}()</span>
                  <StatusBadge tone={fileTone(fn.status)}>
                    {statusLabel(fn.status, ar)}
                  </StatusBadge>
                </div>
              )) : (
                <p className="empty-note">{ar ? 'لا توجد دوال في هذا الملف.' : 'No functions'}</p>
              )}
            </section>
            <button
              className="button button-primary button-wide"
              onClick={() => onStage('scan')}
              type="button"
            >
              {ar ? 'التالي: مراجعة الفحص' : 'Next: review scanner'}
              <Icon name="arrow" />
            </button>
          </>
        ) : null}

        {workflowId === 'scan' ? (
          <>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'الفحص الأمني' : 'SCANNER'}</span>
              <h3 className="technical-value">
                {data.scan.profile} · {data.scan.coverage} coverage
              </h3>
              <p>
                {ar
                  ? 'التغطية والقواعد والنتائج معروضة في سياق واحد مرتبط بالكود.'
                  : 'Coverage, rules, and findings stay connected to the code context.'}
              </p>
            </section>
            <section className="inspector-section key-value-grid">
              <div><span>{ar ? 'الملفات' : 'Files'}</span><strong>{data.scan.filesCovered}</strong></div>
              <div><span>{ar ? 'الدوال' : 'Functions'}</span><strong>{data.scan.functionsCovered}</strong></div>
              <div><span>{ar ? 'القواعد المنفذة' : 'Rules executed'}</span><strong>{data.scan.rulesExecuted}</strong></div>
              <div><span>{ar ? 'القواعد غير المجتازة' : 'Failed'}</span><strong>{data.scan.rulesFailed}</strong></div>
            </section>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'المعايير' : 'STANDARDS'}</span>
              <div className="role-pills technical-pills">
                {data.scan.standards.map((item) => <span key={item}>{item}</span>)}
              </div>
            </section>
            <section className="inspector-section evidence-box">
              <span className="section-label">{ar ? 'عقد الفلاتر' : 'FILTER CONTRACT'}</span>
              <strong className="technical-value">{data.scan.filtersSource}</strong>
              <p>
                {ar
                  ? 'قوة الفلاتر وقواعدها ستأتي من الـBackend لاحقًا، وليست مثبتة داخل React.'
                  : 'Filter strength and rules will come from the backend contract, not from React.'}
              </p>
            </section>
            <button
              className="button button-primary button-wide"
              onClick={() => onStage('investigate')}
              type="button"
            >
              {ar ? 'التالي: التحقيق في النتيجة' : 'Next: investigate finding'}
              <Icon name="arrow" />
            </button>
          </>
        ) : null}

        {workflowId === 'investigate' ? (
          finding ? (
            <>
              <section className="inspector-section finding-title-block">
                <span className="section-label technical-value">{finding.cwe}</span>
                <h3>{ar ? finding.titleAr ?? finding.title : finding.title}</h3>
                <p>{ar ? finding.rootCauseAr ?? finding.rootCause : finding.rootCause}</p>
              </section>

              <section className="inspector-section key-value-grid">
                <div>
                  <span>{ar ? 'الدالة' : 'Function'}</span>
                  <strong className="technical-value">
                    {finding.function ?? (ar ? 'إعدادات' : 'Configuration')}
                  </strong>
                </div>
                <div><span>{ar ? 'السطر' : 'Line'}</span><strong>{finding.line}</strong></div>
                <div>
                  <span>{ar ? 'المصدر' : 'Source'}</span>
                  <strong className="technical-value">{finding.source}</strong>
                </div>
                <div>
                  <span>{ar ? 'المصب' : 'Sink'}</span>
                  <strong className="technical-value">{finding.sink}</strong>
                </div>
              </section>

              <section className="inspector-section">
                <span className="section-label">{ar ? 'مسار التتبع' : 'TRACE'}</span>
                <div className="trace-list">
                  {finding.trace.map((step, index) => (
                    <div className="trace-step" key={`${finding.id}-${step}`}>
                      <span>{index + 1}</span>
                      <strong className="technical-value">{step}</strong>
                    </div>
                  ))}
                </div>
              </section>

              <section className="inspector-section">
                <span className="section-label">{ar ? 'المعيار' : 'STANDARD'}</span>
                <p className="technical-value technical-wrap">{finding.standard}</p>
              </section>

              <section className="inspector-section evidence-box">
                <span className="section-label">{ar ? 'الدليل' : 'EVIDENCE'}</span>
                <strong>
                  {ar ? finding.exploitabilityAr ?? finding.exploitability : finding.exploitability}
                </strong>
                <p>{ar ? finding.evidenceAr ?? finding.evidence : finding.evidence}</p>
              </section>

              <button
                className="button button-primary button-wide"
                onClick={() => onStage('transform')}
                type="button"
              >
                {ar ? 'عرض النسخة المقترحة' : 'Review secure candidate'}
                <Icon name="arrow" />
              </button>
            </>
          ) : (
            <section className="inspector-section">
              <h3>{ar ? 'لا توجد نتيجة محددة لهذا العنصر.' : 'No finding is selected for this element.'}</h3>
              <p>{ar ? 'اختر نتيجة من قائمة المشروع.' : 'Choose a finding from the project list.'}</p>
            </section>
          )
        ) : null}

        {workflowId === 'transform' && finding ? (
          <>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'السبب الجذري' : 'ROOT CAUSE'}</span>
              <p>{ar ? finding.rootCauseAr ?? finding.rootCause : finding.rootCause}</p>
            </section>
            <section className="inspector-section key-value-grid">
              <div>
                <span>{ar ? 'الأسطر المتأثرة' : 'Changed'}</span>
                <strong>{finding.changedLines}</strong>
              </div>
              <div>
                <span>{ar ? 'الحالة' : 'State'}</span>
                <strong>{ar ? 'يتطلب التحقق' : 'Verification required'}</strong>
              </div>
            </section>
            <section className="inspector-section evidence-box">
              <span className="section-label">{ar ? 'القاعدة الأمنية' : 'SECURITY RULE'}</span>
              <strong className="technical-value technical-wrap">{finding.standard}</strong>
              <p>
                {ar
                  ? 'هذه نسخة مقترحة فقط. لا تُعتبر معالجة ناجحة حتى تنجح مرحلة التحقق.'
                  : 'This is a candidate only. It is not considered remediated until verification succeeds.'}
              </p>
            </section>
            <UpdatedFileDownload ar={ar} compact finding={finding} />
            <button
              className="button button-primary button-wide"
              onClick={() => onStage('verify')}
              type="button"
            >
              {ar ? 'التالي: التحقق من الإصلاح' : 'Next: verify remediation'}
              <Icon name="arrow" />
            </button>
          </>
        ) : null}

        {workflowId === 'verify' && finding ? (
          <>
            <section className="inspector-section verification-summary">
              <span className="section-label">{ar ? 'التحقق' : 'VERIFICATION'}</span>
              <h3>
                {ar
                  ? finding.verification.closure === 'Verified remediated'
                    ? 'تم التحقق من المعالجة'
                    : 'نسخة مرشحة بانتظار التحقق'
                  : finding.verification.closure}
              </h3>
              <p>
                {ar
                  ? 'قرار الإغلاق لا يعتمد على اقتراح الذكاء الاصطناعي؛ يعتمد على إعادة الفحص والأدلة.'
                  : 'Closure does not rely on the AI suggestion. It relies on re-scan and evidence.'}
              </p>
            </section>
            <div className="verification-list">
              {Object.entries(finding.verification)
                .filter(([key]) => key !== 'closure')
                .map(([key, value]) => (
                  <div className="verification-row" key={key}>
                    <span>{verificationKeyLabel(key, ar)}</span>
                    <strong>{verificationValueLabel(value, ar)}</strong>
                  </div>
                ))}
            </div>
            <UpdatedFileDownload ar={ar} compact finding={finding} />
            <button
              className="button button-primary button-wide"
              onClick={() => onStage('report')}
              type="button"
            >
              {ar ? 'التالي: التقرير' : 'Next: report'}
              <Icon name="arrow" />
            </button>
          </>
        ) : null}

        {workflowId === 'report' ? (
          <>
            <section className="inspector-section">
              <span className="section-label">{ar ? 'التقرير' : 'REPORT'}</span>
              <h3>{ar ? 'النتيجة أصبحت قابلة للمراجعة.' : 'The result is now reviewable.'}</h3>
              <p>
                {ar
                  ? 'التقرير يفصل بين ما تم إصلاحه، وما بقي، وما لم يتم إثباته بعد.'
                  : 'The report separates remediated, remaining, and not-yet-proven items.'}
              </p>
            </section>
            <button className="button button-primary button-wide" onClick={onOpenReport} type="button">
              {ar ? 'فتح التقرير الأمني' : 'Open security report'}
              <Icon name="report" />
            </button>
          </>
        ) : null}
      </div>
    </aside>
  );
}
