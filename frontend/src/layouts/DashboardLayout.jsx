import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { useAuth } from '../contexts/AuthContext';

const DashboardLayout = () => {
  const { userRole } = useAuth();
  
  return (
    <div className="min-h-screen bg-gray-100">
      <Sidebar />
      
      <div className="flex">
        <Sidebar userRole={userRole} />
        
        <div className="flex-1 p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;