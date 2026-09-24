import { useLanguage } from '../i18n';
import Icon from './Icon';

export default function AsyncState({
  error,
  loading,
  empty,
  onRetry,
  loadingLabel = 'Loading…',
  emptyLabel = 'No data available.',
}) {
  const { language } = useLanguage();
  const ar = language === 'ar';

  if (loading) {
    return (
      <div aria-live="polite" className="async-state">
        <span className="activity-dot" />
        <strong>{loadingLabel}</strong>
      </div>
    );
  }

  if (error) {
    return (
      <div aria-live="polite" className="async-state async-error">
        <Icon name="alert" />
        <div>
          <strong>{ar ? 'تعذر تحميل هذه الصفحة.' : 'Unable to load this view.'}</strong>
          <span>{error.message}</span>
        </div>
        {onRetry ? (
          <button className="button button-secondary" onClick={onRetry} type="button">
            {ar ? 'إعادة المحاولة' : 'Retry'}
          </button>
        ) : null}
      </div>
    );
  }

  if (empty) {
    return (
      <div className="async-state">
        <Icon name="info" />
        <strong>{emptyLabel}</strong>
      </div>
    );
  }

  return null;
}
