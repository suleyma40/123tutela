import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import DiagnosisPage from './pages/DiagnosisPage';
import PaymentPage from './pages/PaymentPage';
import SuccessPage from './pages/SuccessPage';
import AdminPanel from './pages/AdminPanel';
import AdminCaseDetail from './pages/AdminCaseDetail';
import LegalPageView from './views/LegalPageView';
import SurveyTestPage from './pages/SurveyTestPage';
import { trackEvent } from './lib/analytics';

function AnalyticsTracker() {
  const location = useLocation();
  React.useEffect(() => {
    trackEvent('page_view', { path: location.pathname, query: location.search || '' });
  }, [location.pathname, location.search]);
  return null;
}

function App() {
  return (
    <Router>
      <AnalyticsTracker />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/diagnostico" element={<DiagnosisPage />} />
        <Route path="/pago" element={<PaymentPage />} />
        <Route path="/pago/resultado" element={<SuccessPage />} />
        <Route path="/gracias" element={<SuccessPage />} />
        <Route path="/terminos" element={<LegalPageView page="terminos" onBackHome={() => window.history.back()} />} />
        <Route path="/privacidad" element={<LegalPageView page="privacidad" onBackHome={() => window.history.back()} />} />
        <Route path="/contacto" element={<LegalPageView page="contacto" onBackHome={() => window.history.back()} />} />
        <Route path="/testeo" element={<Navigate to="/diagnostico?test_code=TEST123" replace />} />
        <Route path="/testeo/encuesta" element={<SurveyTestPage />} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        <Route path="/admin" element={<AdminPanel />} />
        <Route path="/admin/caso/:id" element={<AdminCaseDetail />} />
        <Route path="/equipo" element={<AdminPanel />} />
        <Route path="/equipo/caso/:id" element={<AdminCaseDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
