import { useEffect, useRef, useState } from 'react';
import { getConfigurationStatus, getFindingAdvice } from '../api/endpoints';
import Icon from './Icon';

function AdviceList({ title, items }) {
  if (!items?.length) return null;
  return <section><h3>{title}</h3><ul>{items.map((item, index) => <li key={`${index}:${item}`}>{item}</li>)}</ul></section>;
}

export default function AdvisorDrawer({ open, onClose, onSettings, analysisId, findingId, filePath, ar }) {
  const dialogRef = useRef(null);
  const [configuration, setConfiguration] = useState(null);
  const [configurationError, setConfigurationError] = useState(false);
  const [advice, setAdvice] = useState(null);
  const [busy, setBusy] = useState(false);
  const [requestError, setRequestError] = useState('');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;
    let active = true;
    setConfiguration(null);
    setConfigurationError(false);
    getConfigurationStatus()
      .then((result) => { if (active) setConfiguration(result); })
      .catch(() => { if (active) setConfigurationError(true); });
    return () => { active = false; };
  }, [open]);

  useEffect(() => {
    setAdvice(null);
    setRequestError('');
  }, [analysisId, findingId, filePath]);

  const configured = configuration?.ai?.enabled && configuration?.ai?.key_configured && configuration?.ai?.model_configured;
  const selectedFinding = Boolean(analysisId && findingId && filePath);

  async function requestAdvice() {
    if (!configured || !selectedFinding || busy) return;
    setBusy(true);
    setRequestError('');
    setAdvice(null);
    try {
      const response = await getFindingAdvice({ analysisId, findingId, filePath });
      if (response.result?.authority !== 'ADVISORY_ONLY') throw new Error('Unexpected advisor response.');
      setAdvice(response);
    } catch (error) {
      setRequestError(error?.code === 'ADVISOR_QUOTA_UNAVAILABLE'
        ? (ar ? 'المفتاح متصل، لكن رصيد مشروع OpenAI API نفد. أضف رصيدًا للمشروع ثم أعد المحاولة.' : 'The key is connected, but the OpenAI API project has no remaining credits. Add credits to that project and retry.')
        : error instanceof Error ? error.message : 'Advisory request failed.');
    } finally {
      setBusy(false);
    }
  }

  return <dialog aria-labelledby="advisor-drawer-title" className="advisor-drawer" id="advisor-drawer" onClose={onClose} onClick={(event) => { if (event.target === dialogRef.current) onClose(); }} ref={dialogRef}>
    <div className="advisor-drawer-head"><div><span className="eyebrow">RAQEEB / AI</span><h2 id="advisor-drawer-title">{ar ? 'مراجعة AI للنتيجة' : 'AI finding review'}</h2></div><button aria-label={ar ? 'إغلاق المساعد' : 'Close advisor'} className="icon-button" onClick={onClose} type="button"><Icon name="close" /></button></div>
    <div className="advisor-drawer-body">
      <span className="candidate-state">ADVISORY ONLY</span>
      <p>{ar ? 'يرسل رقيب الدليل البنيوي المحدود لهذه النتيجة إلى OpenAI عند طلبك فقط. لا يرسل الملف الخام، ولا يغيّر حالة الثغرة أو يطبّق الإصلاح.' : 'Only when requested, Raqeeb sends bounded structured evidence for this finding to OpenAI. It does not send the raw file, change finding status, or apply a patch.'}</p>
      {configurationError ? <p role="alert">{ar ? 'تعذر قراءة حالة الاتصال.' : 'Connection status could not be loaded.'}</p> : !configuration ? <p role="status">{ar ? 'جارٍ فحص حالة الاتصال…' : 'Checking connection…'}</p> : <p>{ar ? 'الموديل: ' : 'Model: '}{configuration.ai.model ?? 'UNSET'} · {configured ? (ar ? 'مهيأ على الخادم' : 'Server configured') : (ar ? 'غير مهيأ' : 'Not configured')}</p>}
      {!selectedFinding && <p>{ar ? 'افتح نتيجة محددة من قائمة المرشحات لتطلب مراجعة لها.' : 'Open a specific finding to request an advisory review.'}</p>}
      <button className="button button-primary" disabled={!configured || !selectedFinding || busy} onClick={requestAdvice} type="button">{busy ? (ar ? 'جارٍ طلب المراجعة…' : 'Requesting review…') : (ar ? 'حلّل هذه النتيجة بـAI' : 'Analyze this finding with AI')}</button>
      {requestError && <p className="form-error" role="alert">{requestError}</p>}
      {advice && <div className="advisor-response" role="status"><span className="eyebrow">{ar ? 'اقتراح استشاري غير متحقق' : 'Unverified advisory suggestion'}</span><AdviceList items={advice.result.advice.root_cause_hypotheses} title={ar ? 'فرضيات السبب' : 'Root-cause hypotheses'} /><section><h3>{ar ? 'استراتيجية تعديل محدود' : 'Minimal patch strategy'}</h3><p>{advice.result.advice.patch_strategy}</p></section><AdviceList items={advice.result.advice.test_suggestions} title={ar ? 'اختبارات مقترحة' : 'Suggested tests'} /><AdviceList items={advice.result.advice.uncertainties} title={ar ? 'ما لم يُثبت' : 'Uncertainties'} /><small>{ar ? 'السياق المرسل: ' : 'Context sent: '}{advice.context_budget.characters} {ar ? 'حرفًا تقريبًا. الرد غير محفوظ في سجل التحليل.' : 'characters approximately. This response is not saved in the analysis record.'}</small></div>}
      <button className="button button-secondary" onClick={onSettings} type="button">{ar ? 'إعدادات الربط' : 'Connection settings'}</button>
    </div>
  </dialog>;
}
