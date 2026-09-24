import { useLanguage } from '../i18n';
import Icon from './Icon';

export default function WorkflowBar({ stages, currentId, onSelect }) {
  const { language } = useLanguage();
  const ar = language === 'ar';
  const currentIndex = stages.findIndex((stage) => stage.id === currentId);

  return (
    <div
      aria-label={ar ? 'تسلسل المراجعة الأمنية' : 'Security workflow'}
      className="workflow-bar"
    >
      {stages.map((stage, index) => {
        const state = index < currentIndex
          ? 'done'
          : index === currentIndex
            ? 'current'
            : 'waiting';
        const enabled = index <= currentIndex;

        return (
          <button
            aria-current={state === 'current' ? 'step' : undefined}
            className={`workflow-step workflow-${state}`}
            disabled={!enabled}
            key={stage.id}
            onClick={() => enabled && onSelect?.(stage.id)}
            type="button"
          >
            <span className="workflow-index">
              {state === 'done' ? <Icon name="check" size={15} /> : index + 1}
            </span>
            <span>{ar ? stage.labelAr ?? stage.label : stage.label}</span>
          </button>
        );
      })}
    </div>
  );
}
