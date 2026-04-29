import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import DiagnosisPage from './pages/DiagnosisPage';
import PaymentPage from './pages/PaymentPage';
import SuccessPage from './pages/SuccessPage';
import AdminPanel from './pages/AdminPanel';
import AdminCaseDetail from './pages/AdminCaseDetail';
import LegalPageView from './views/LegalPageView';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/diagnostico" element={<DiagnosisPage />} />
        <Route path="/pago" element={<PaymentPage />} />
        <Route path="/pago/resultado" element={<SuccessPage />} />
        <Route path="/gracias" element={<SuccessPage />} />
        <Route path="/terminos" element={<LegalPageView page="terminos" onBackHome={() => window.history.back()} />} />
        <Route path="/privacidad" element={<LegalPageView page="privacidad" onBackHome={() => window.history.back()} />} />
        <Route path="/contacto" element={<LegalPageView page="contacto" onBackHome={() => window.history.back()} />} />
        <Route path="/admin" element={<AdminPanel />} />
        <Route path="/admin/caso/:id" element={<AdminCaseDetail />} />
        <Route path="/equipo" element={<AdminPanel />} />
        <Route path="/equipo/caso/:id" element={<AdminCaseDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
