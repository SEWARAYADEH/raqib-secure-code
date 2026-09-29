import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import AccountPage from './pages/AccountPage';
import AnalysisProgressPage from './pages/AnalysisProgressPage';
import ConfigurationPage from './pages/ConfigurationPage';
import FindingDetailPage from './pages/FindingDetailPage';
import FindingsPage from './pages/FindingsPage';
import HowItWorksPage from './pages/HowItWorksPage';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import NewAnalysisPage from './pages/NewAnalysisPage';
import ProjectsPage from './pages/ProjectsPage';
import ReportPage from './pages/ReportPage';
import SecurityTrustPage from './pages/SecurityTrustPage';
import SystemStatePage from './pages/SystemStatePage';
import TwoFactorPage from './pages/TwoFactorPage';
import WorkbenchPage from './pages/WorkbenchPage';

function protectedPage(element) {
  return <ProtectedRoute>{element}</ProtectedRoute>;
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<LandingPage />} path="/" />
      <Route element={<HowItWorksPage />} path="/how-it-works" />
      <Route element={<SecurityTrustPage />} path="/security-trust" />
      <Route element={<LoginPage />} path="/login" />
      <Route element={<Navigate replace to="/login?mode=code" />} path="/create-account" />
      <Route element={<Navigate replace to="/login?mode=code" />} path="/verify-email" />
      <Route element={<TwoFactorPage />} path="/two-factor" />
      <Route element={<Navigate replace to="/login?mode=code" />} path="/forgot-password" />
      <Route element={<Navigate replace to="/login?mode=code" />} path="/reset-password" />

      <Route element={protectedPage(<ProjectsPage />)} path="/projects" />
      <Route element={protectedPage(<NewAnalysisPage />)} path="/analysis/new" />
      <Route element={protectedPage(<AnalysisProgressPage />)} path="/analysis/progress" />
      <Route element={protectedPage(<AnalysisProgressPage />)} path="/analysis/progress/:analysisId" />
      <Route element={protectedPage(<ConfigurationPage />)} path="/configuration" />
      <Route element={protectedPage(<AccountPage />)} path="/account" />
      <Route element={protectedPage(<FindingsPage />)} path="/projects/:projectId/findings" />
      <Route element={protectedPage(<FindingDetailPage />)} path="/projects/:projectId/findings/:findingId" />
      <Route element={protectedPage(<WorkbenchPage />)} path="/projects/:projectId/workbench" />
      <Route element={protectedPage(<ReportPage />)} path="/projects/:projectId/report" />

      <Route element={<Navigate replace to="/projects" />} path="/dashboard" />
      <Route element={<SystemStatePage type="unauthorized" />} path="/unauthorized" />
      <Route element={<SystemStatePage type="forbidden" />} path="/forbidden" />
      <Route element={<SystemStatePage type="notFound" />} path="*" />
    </Routes>
  );
}
