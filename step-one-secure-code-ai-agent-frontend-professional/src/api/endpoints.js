import { apiRequest, mockRequest } from './client';
import {
  mockAnalysisOptions,
  mockAnalysisProgress,
  mockConfiguration,
  mockFindings,
  mockLiveOperation,
  mockProjects,
  mockReport,
  mockScanSummary,
  mockTechnologyProfile,
  mockWorkspaceFiles,
  projectPassport,
  workflowStages,
} from '../mock/data';

export const getProjects = () => mockRequest(mockProjects);

export const getAnalysisOptions = () => mockRequest(mockAnalysisOptions);
export const getAnalysisProgress = () => mockRequest(mockAnalysisProgress);

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

export const getWorkbench = () => {
  return mockRequest({
    passport: projectPassport,
    files: mockWorkspaceFiles,
    findings: mockFindings,
    workflow: workflowStages,
    technology: mockTechnologyProfile,
    scan: mockScanSummary,
    liveOperation: mockLiveOperation,
  });
};

export const getReport = () => mockRequest(mockReport);
export const getConfiguration = () => mockRequest(mockConfiguration);
