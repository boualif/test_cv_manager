import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ allowedRoles }) => {
  const { currentUser, userRole, loading } = useAuth();
  const location = useLocation();

  // Show loading screen while auth is being checked
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Check if user is authenticated
  if (!currentUser) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user has allowed role (case-insensitive)
  if (!allowedRoles.map(r => r.toLowerCase()).includes(userRole)) {
    // Redirect based on user role
    switch (userRole) {
      case 'admin':
        return <Navigate to="/admin/dashboard" replace />;
      case 'recruiter':
        return <Navigate to="/recruiter/dashboard" replace />;
      case 'sales':
        return <Navigate to="/sales/dashboard" replace />;
      case 'hr':
        return <Navigate to="/hr/dashboard" replace />;
      default:
        return <Navigate to="/login" replace />;
    }
  }

  // User is authenticated and authorized
  return <Outlet />;
};

export default ProtectedRoute;
