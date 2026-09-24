import Icon from './Icon';
import StatusBadge from './StatusBadge';

function fileTone(status) {
  if (status === 'critical') return 'danger';
  if (status === 'warning') return 'warning';
  return 'success';
}

function severityTone(severity) {
  if (severity === 'Critical') return 'danger';
  if (severity === 'High') return 'warning';
  return 'info';
}

function fileStatusLabel(status, ar) {
  if (!ar) return status;
  if (status === 'critical') return 'حرج';
  if (status === 'warning') return 'مراجعة';
  return 'آمن';
}

function severityLabel(severity, ar) {
  if (!ar) return severity;
  if (severity === 'Critical') return 'حرجة';
  if (severity === 'High') return 'عالية';
  return 'متوسطة';
}

export default function WorkbenchExplorer({
  ar,
  data,
  file,
  fileFilter,
  fileSearch,
  filteredFiles,
  onChooseFinding,
  onFileFilter,
  onFileSearch,
  onSelectFile,
  onSelectFunction,
  selectedFindingId,
  selectedFunction,
}) {
  return (
    <aside className="explorer-pane">
      <div className="pane-heading">
        <div>
          <span className="eyebrow">{ar ? 'المشروع' : 'PROJECT'}</span>
          <strong>{data.passport.name}</strong>
        </div>
        <Icon name="search" size={17} />
      </div>

      <div className="explorer-tools">
        <label className="compact-search">
          <Icon name="search" size={16} />
          <input
            aria-label={ar ? 'بحث في الملفات' : 'Search files'}
            onChange={(event) => onFileSearch(event.target.value)}
            placeholder={ar ? 'ابحث عن ملف…' : 'Search files…'}
            type="search"
            value={fileSearch}
          />
        </label>
        <select
          aria-label={ar ? 'فلترة الملفات' : 'Filter files'}
          onChange={(event) => onFileFilter(event.target.value)}
          value={fileFilter}
        >
          <option value="all">{ar ? 'الكل' : 'All'}</option>
          <option value="issues">{ar ? 'تحتاج مراجعة' : 'Issues'}</option>
          <option value="safe">{ar ? 'آمنة' : 'Safe'}</option>
        </select>
      </div>

      <div className="explorer-section">
        <span className="section-label">{ar ? 'الملفات' : 'FILES'}</span>
        <div className="file-list">
          {filteredFiles.map((item) => (
            <button
              className={`file-row${item.id === file.id ? ' active' : ''}`}
              key={item.id}
              onClick={() => onSelectFile(item)}
              type="button"
            >
              <Icon name="file" size={17} />
              <span className="file-row-copy technical-block">
                <strong>{item.name}</strong>
                <small>{item.path}</small>
              </span>
              <StatusBadge tone={fileTone(item.status)}>
                {item.findings.length || fileStatusLabel(item.status, ar)}
              </StatusBadge>
            </button>
          ))}
        </div>
      </div>

      <div className="explorer-section">
        <span className="section-label">{ar ? 'الدوال' : 'FUNCTIONS'}</span>
        {file.functions.length ? (
          <div className="function-list">
            {file.functions.map((fn) => (
              <button
                className={`function-row${selectedFunction === fn.name ? ' active' : ''}`}
                key={fn.name}
                onClick={() => onSelectFunction(fn)}
                type="button"
              >
                <Icon name="function" size={16} />
                <span className="technical-block">
                  <strong>{fn.name}()</strong>
                  <small>{ar ? `السطر ${fn.line}` : `line ${fn.line}`}</small>
                </span>
                <span
                  aria-label={fileStatusLabel(fn.status, ar)}
                  className={`function-dot dot-${fn.status}`}
                  title={fileStatusLabel(fn.status, ar)}
                />
              </button>
            ))}
          </div>
        ) : (
          <p className="empty-note">
            {ar ? 'لا توجد دوال في هذا الملف.' : 'No functions in this file.'}
          </p>
        )}
      </div>

      <div className="explorer-section findings-quicklist">
        <span className="section-label">{ar ? 'النتائج' : 'FINDINGS'}</span>
        {data.findings.map((item) => (
          <button
            className={`finding-quick${selectedFindingId === item.id ? ' active' : ''}`}
            key={item.id}
            onClick={() => onChooseFinding(item)}
            type="button"
          >
            <span className="technical-value">{item.id}</span>
            <strong>{ar ? item.titleAr ?? item.title : item.title}</strong>
            <StatusBadge tone={severityTone(item.severity)}>
              {severityLabel(item.severity, ar)}
            </StatusBadge>
          </button>
        ))}
      </div>
    </aside>
  );
}
