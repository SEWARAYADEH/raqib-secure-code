import { useMemo, useState } from 'react';
import { downloadUpdatedCode, generateUpdatedFileName } from '../utils/fileDownload';
import Icon from './Icon';

export default function UpdatedFileDownload({ ar, finding, compact = false }) {
  const [state, setState] = useState('idle');
  const [error, setError] = useState('');
  const originalName = finding?.originalFileName ?? '';
  const content = finding?.updatedFileContent ?? '';
  const hasUpdatedFile = Boolean(originalName && content);
  const updatedName = useMemo(() => {
    if (!originalName) return '';
    return generateUpdatedFileName(originalName, finding?.updateAction);
  }, [finding?.updateAction, originalName]);

  const handleDownload = () => {
    if (!hasUpdatedFile || state === 'preparing') return;

    setState('preparing');
    setError('');

    try {
      downloadUpdatedCode({
        originalName,
        action: finding?.updateAction,
        content,
      });
      setState('idle');
    } catch {
      setState('error');
      setError(
        ar
          ? 'تعذر تجهيز الملف المعدّل. حاول مرة أخرى.'
          : 'Unable to prepare the updated file. Try again.',
      );
    }
  };

  return (
    <section className={`updated-file-card${compact ? ' compact' : ''}`}>
      <div className="updated-file-heading">
        <div>
          <span className="section-label">
            {ar ? 'الملف المعدّل' : 'UPDATED FILE'}
          </span>
          <strong>
            {ar
              ? 'نزّل النسخة الناتجة بدون المساس بالملف الأصلي.'
              : 'Download the resulting file without changing the original.'}
          </strong>
        </div>
        <Icon name="file" size={18} />
      </div>

      <dl className="updated-file-meta">
        <div>
          <dt>{ar ? 'الملف الأصلي' : 'Original file'}</dt>
          <dd className="technical-value">{originalName || '—'}</dd>
        </div>
        <div>
          <dt>{ar ? 'الملف المعدّل' : 'Updated file'}</dt>
          <dd className="technical-value">{updatedName || '—'}</dd>
        </div>
        <div>
          <dt>{ar ? 'اللغة' : 'Language'}</dt>
          <dd className="technical-value">{finding?.language ?? '—'}</dd>
        </div>
        <div>
          <dt>{ar ? 'التعديل' : 'Modification'}</dt>
          <dd>{
            ar
              ? finding?.modificationAr ?? finding?.modification ?? '—'
              : finding?.modification ?? '—'
          }</dd>
        </div>
      </dl>

      <button
        className="button button-secondary button-wide updated-file-action"
        disabled={!hasUpdatedFile || state === 'preparing'}
        onClick={handleDownload}
        type="button"
      >
        <Icon name="download" />
        {state === 'preparing'
          ? ar ? 'تجهيز الملف…' : 'Preparing file…'
          : ar ? 'تحميل الملف المعدّل' : 'Download Updated File'}
      </button>

      {!hasUpdatedFile ? (
        <p className="updated-file-note">
          {ar
            ? 'يتفعّل التحميل عند توفر محتوى النسخة المعدّلة.'
            : 'Download becomes available when updated code content exists.'}
        </p>
      ) : null}

      {error ? <p className="form-error updated-file-error" role="alert">{error}</p> : null}
    </section>
  );
}
