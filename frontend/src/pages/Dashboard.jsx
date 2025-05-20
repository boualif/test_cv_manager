import React, { useState, useEffect } from 'react';
import axios from 'axios';
import CandidateList from '../components/CandidateList';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalCandidates: 0,
    recentUploads: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/candidates');
        setStats({
          totalCandidates: response.data.length,
          recentUploads: response.data.filter(
            c => new Date(c.created_at).getTime() > Date.now() - 7 * 24 * 60 * 60 * 1000
          ).length // Candidates from last 7 days
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-gray-500 text-sm font-medium uppercase mb-2">Total Candidates</h3>
          <div className="flex items-center">
            <div className="text-3xl font-bold text-gray-900 mr-2">{stats.totalCandidates}</div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-gray-500 text-sm font-medium uppercase mb-2">Recent Uploads (7 days)</h3>
          <div className="flex items-center">
            <div className="text-3xl font-bold text-gray-900 mr-2">{stats.recentUploads}</div>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-bold mb-4">Candidate List</h2>
        <CandidateList />
      </div>
    </div>
  );
};

export default Dashboard;