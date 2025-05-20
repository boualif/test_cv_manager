import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const RoleRedirect = () => {
  const { userRole, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading) {
      switch (userRole) {
        case 'admin':
          navigate('/admin/dashboard');
          break;
        case 'recruiter':
          navigate('/recruiter/dashboard');
          break;
        case 'sales':
          navigate('/sales/dashboard');
          break;
        case 'hr':
          navigate('/hr/dashboard');
          break;
        default:
          navigate('/login');
      }
    }
  }, [userRole, loading, navigate]);

  return (
    <div className="flex justify-center items-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
  );
};

export default RoleRedirect;