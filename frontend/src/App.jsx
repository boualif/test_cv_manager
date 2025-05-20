import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import AdminDashboard from "./pages/admin/Dashboard";
import UserManagement from "./pages/admin/UserManagement";
import RecruiterDashboard from "./pages/recruiter/Dashboard";
import SalesDashboard from "./pages/sales/Dashboard";
import HRDashboard from "./pages/hr/Dashboard";
import CandidateProfile from './pages/CandidateProfile';
import UploadCV from './pages/UploadCV';
import CandidateList from './components/CandidateList';

// Import Job Management Components
import JobList from './pages/JobList';
import JobForm from './pages/JobForm';
import JobDetail from './pages/JobDetail';
import JobMatchAnalysis from './pages/JobMatchAnalysis';

import "./styles.css";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Routes publiques */}
          <Route path="/login" element={<Login />} />
          
          {/* Routes protégées pour l'administrateur */}
          <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/users" element={<UserManagement />} />
            <Route path="/admin/upload" element={<UploadCV />}/>
            <Route path="/admin/candidates" element={<CandidateList />}/>
          </Route>
          
          {/* Routes protégées pour le recruteur */}
          <Route element={<ProtectedRoute allowedRoles={['recruiter', 'admin']} />}>
            <Route path="/recruiter/dashboard" element={<RecruiterDashboard />} />
            <Route path="/upload" element={<UploadCV />} />
          </Route>
          
          {/* Routes protégées pour le commercial */}
          <Route element={<ProtectedRoute allowedRoles={['sales', 'admin']} />}>
            <Route path="/sales/dashboard" element={<SalesDashboard />} />
            <Route path="/sales/upload" element={<UploadCV />} />
            <Route path="/sales/candidates/:id" element={<CandidateProfile />} />
          </Route>
          
          {/* Routes protégées pour les RH */}
          <Route element={<ProtectedRoute allowedRoles={['hr', 'admin']} />}>
            <Route path="/hr/dashboard" element={<HRDashboard />} />
            <Route path="/hr/upload" element={<UploadCV />} />
            <Route path="/hr/candidates/:id" element={<CandidateProfile />} />
          </Route>
          
          {/* Routes protégées pour tous les utilisateurs authentifiés */}
          <Route element={<ProtectedRoute allowedRoles={['admin', 'recruiter', 'sales', 'hr']} />}>
            <Route path="/candidates" element={<CandidateList />} /> 
            <Route path="/candidates/:id" element={<CandidateProfile />} />
            <Route path="/upload" element={<UploadCV />} />
            
            {/* Job Management Routes */}
            <Route path="/jobs" element={<JobList />} />
            <Route path="/jobs/create" element={<JobForm />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="/jobs/:id/edit" element={<JobForm />} />
            <Route path="/jobs/:id/match" element={<JobMatchAnalysis />} />
          </Route>
          
          {/* Redirection par défaut */}
          <Route path="/" element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        
        {/* Toast Container for notifications */}
        <ToastContainer 
          position="top-right" 
          autoClose={3000} 
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </Router>
    </AuthProvider>
  );
}

export default App;