import React from 'react';
import Sidebar from '../../components/Sidebar';

const RecruiterDashboard = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Sidebar />
      <div className="container mx-auto p-6 flex-grow">
        <h1 className="text-2xl font-bold mb-6">Recruiter Dashboard</h1>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <p>Welcome to the Recruiter Dashboard. Here you can manage candidate information and upload CVs.</p>
        </div>
      </div>
    </div>
  );
};

export default RecruiterDashboard;