import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import DiagnosisPage from './pages/DiagnosisPage';
import PaymentPage from './pages/PaymentPage';
import SuccessPage from './pages/SuccessPage';
import AdminPanel from './pages/AdminPanel';
import AdminCaseDetail from './pages/AdminCaseDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/diagnostico" element={<DiagnosisPage />} />
        <Route path="/pago" element={<PaymentPage />} />
        <Route path="/pago/resultado" element={<SuccessPage />} />
        <Route path="/gracias" element={<SuccessPage />} />
        <Route path="/admin" element={<AdminPanel />} />
        <Route path="/admin/caso/:id" element={<AdminCaseDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
