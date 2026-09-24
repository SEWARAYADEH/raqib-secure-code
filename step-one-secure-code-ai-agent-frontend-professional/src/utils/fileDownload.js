const MIME_BY_EXTENSION = {
  '.py': 'text/x-python;charset=utf-8',
  '.js': 'text/javascript;charset=utf-8',
  '.jsx': 'text/jsx;charset=utf-8',
  '.ts': 'text/typescript;charset=utf-8',
  '.tsx': 'text/tsx;charset=utf-8',
  '.php': 'application/x-httpd-php;charset=utf-8',
  '.java': 'text/x-java-source;charset=utf-8',
  '.cpp': 'text/x-c++src;charset=utf-8',
  '.cs': 'text/plain;charset=utf-8',
  '.html': 'text/html;charset=utf-8',
  '.css': 'text/css;charset=utf-8',
};

function splitFinalExtension(filename) {
  const value = String(filename ?? '').trim();
  const lastDot = value.lastIndexOf('.');

  if (lastDot <= 0 || lastDot === value.length - 1) {
    return { base: value || 'updated_file', extension: '' };
  }

  return {
    base: value.slice(0, lastDot),
    extension: value.slice(lastDot),
  };
}

function sanitizeBaseName(value) {
  const safe = value
    .normalize('NFKD')
    .replace(/[^A-Za-z0-9._-]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^[_ .-]+|[_ .-]+$/g, '')
    .slice(0, 80);

  return safe || 'updated_file';
}

export function normalizeUpdateAction(action) {
  return String(action ?? '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 48);
}

export function generateUpdatedFileName(originalName, action) {
  const { base, extension } = splitFinalExtension(originalName);
  const safeBase = sanitizeBaseName(base);
  const safeAction = normalizeUpdateAction(action);
  const suffix = safeAction ? `_update_${safeAction}` : '_update';

  return `${safeBase}${suffix}${extension}`;
}

function getMimeType(filename) {
  const { extension } = splitFinalExtension(filename);
  return MIME_BY_EXTENSION[extension.toLowerCase()] ?? 'text/plain;charset=utf-8';
}

export function downloadUpdatedCode({ originalName, action, content }) {
  if (typeof content !== 'string' || content.length === 0) {
    throw new Error('UPDATED_CODE_NOT_AVAILABLE');
  }

  const updatedName = generateUpdatedFileName(originalName, action);
  const blob = new Blob([content], { type: getMimeType(updatedName) });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');

  anchor.href = url;
  anchor.download = updatedName;
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);

  return updatedName;
}
