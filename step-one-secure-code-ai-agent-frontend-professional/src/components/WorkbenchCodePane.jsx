import StatusBadge from './StatusBadge';

function fileTone(status) {
  if (status === 'critical') return 'danger';
  if (status === 'warning') return 'warning';
  return 'success';
}

function fileStatusLabel(status, ar) {
  if (!ar) return status;
  if (status === 'critical') return 'حرج';
  if (status === 'warning') return 'مراجعة';
  return 'آمن';
}

export default function WorkbenchCodePane({
  ar,
  codeLines,
  file,
  finding,
  workflowId,
  zoom,
}) {
  return (
    <section className="code-pane">
      <div className="pane-heading code-heading">
        <div>
          <span className="eyebrow">{ar ? 'الكود' : 'CODE'}</span>
          <strong className="technical-value">{file.path}</strong>
        </div>
        <div className="code-heading-meta">
          <StatusBadge tone={fileTone(file.status)}>
            {fileStatusLabel(file.status, ar)}
          </StatusBadge>
          <span className="technical-value">{file.language}</span>
        </div>
      </div>

      <div className="code-purpose">
        <span>{ar ? 'وظيفة الملف' : 'File purpose'}</span>
        <strong>{ar ? file.purposeAr ?? file.purpose : file.purpose}</strong>
      </div>

      {workflowId === 'transform' && finding ? (
        <div className="workbench-diff" dir="ltr">
          <section>
            <span className="section-label">WEAK CODE</span>
            <pre className="weak-code">{finding.weakCode}</pre>
          </section>
          <section>
            <span className="section-label">SECURE CANDIDATE</span>
            <pre className="secure-code">{finding.secureCode}</pre>
          </section>
        </div>
      ) : (
        <div className="code-viewer" dir="ltr" style={{ fontSize: `${zoom}rem` }}>
          {codeLines.map((line, index) => {
            const lineNumber = index + 1;
            const isFindingLine = finding?.line === lineNumber;

            return (
              <div
                className={`code-line${isFindingLine ? ' finding-line' : ''}`}
                key={`${file.id}-${lineNumber}`}
              >
                <span className="line-number">{lineNumber}</span>
                <code>{line || ' '}</code>
                {isFindingLine ? <span className="line-marker">{finding.id}</span> : null}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
