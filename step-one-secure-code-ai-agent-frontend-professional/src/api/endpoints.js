import { API_BASE_URL, apiRequest } from './client';

export const getProjects = async () => {
  const response = await apiRequest('/api/v1/analyses');
  return response.analyses;
};

export const getAnalysisOptions = () => apiRequest('/api/v1/analysis/options');

export function createAnalysis({ file, scope }) {
  const body = new FormData();
  const isArchive = scope === 'project';
  body.append(isArchive ? 'archive' : 'file', file);

  return apiRequest(
    isArchive
      ? '/api/v1/analysis/archive'
      : '/api/v1/analysis/source',
    {
      method: 'POST',
      body,
    },
  );
}

export function getStoredAnalysis(analysisId) {
  return apiRequest(`/api/v1/analyses/${encodeURIComponent(analysisId)}`);
}

export function createRepairProposal({ analysisId, findingId, file }) {
  const body = new FormData();
  body.append('file', file);
  body.append('finding_id', findingId);
  return apiRequest(`/api/v1/analyses/${encodeURIComponent(analysisId)}/repair-proposal`, {
    method: 'POST',
    body,
  });
}

export function getRepairEvidence(analysisId, findingId) {
  return apiRequest(`/api/v1/analyses/${encodeURIComponent(analysisId)}/repair-evidence/${encodeURIComponent(findingId)}`);
}

function findingLifecyclePath(analysisId, findingId, filePath, download) {
  const query = new URLSearchParams();
  if (filePath) query.set('file', filePath);
  if (download) query.set('download', download);
  return `/api/v1/analyses/${encodeURIComponent(analysisId)}/findings/${encodeURIComponent(findingId)}/lifecycle?${query}`;
}

export function findingLifecycleUrl(analysisId, findingId, filePath, download) {
  return `${API_BASE_URL}${findingLifecyclePath(analysisId, findingId, filePath, download)}`;
}

export function getFindingLifecycle(analysisId, findingId, filePath) {
  return apiRequest(findingLifecyclePath(analysisId, findingId, filePath));
}

export function getFindingAdvice({ analysisId, findingId, filePath }) {
  return apiRequest(`/api/v1/analyses/${encodeURIComponent(analysisId)}/findings/${encodeURIComponent(findingId)}/advice`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath }),
  });
}

export function requestEmailChallenge(email) {
  return apiRequest('/api/v1/auth/email-challenges', {
    method: 'POST',
    body: JSON.stringify({ email }),
    headers: { 'Content-Type': 'application/json' },
  });
}

export function verifyEmailChallenge({ challengeId, code }) {
  return apiRequest('/api/v1/auth/email-challenges/verify', {
    method: 'POST',
    body: JSON.stringify({ challenge_id: challengeId, code }),
    headers: { 'Content-Type': 'application/json' },
  });
}

export function signInWithPassword({ email, password }) {
  return apiRequest('/api/v1/auth/password', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    headers: { 'Content-Type': 'application/json' },
  });
}

export function setAccountPassword({ password, currentPassword }) {
  return apiRequest('/api/v1/auth/password/setup', {
    method: 'POST',
    body: JSON.stringify({ password, current_password: currentPassword }),
    headers: { 'Content-Type': 'application/json' },
  });
}

export function getAuthSession() {
  return apiRequest('/api/v1/auth/session');
}

export function destroyAuthSession() {
  return apiRequest('/api/v1/auth/logout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  });
}

export const getConfigurationStatus = () => apiRequest('/api/v1/configuration/status');
