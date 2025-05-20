import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import Sidebar from '../../components/Sidebar';

const AdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // Commentez cette ligne si l'API n'est pas encore disponible
        // const response = await api.get('/dashboards/admin/dashboard');
        // setDashboardData(response.data);
        
        // Données fictives pour le test (décommentez cette section pour tester l'UI)
        setDashboardData({
          user_stats: {
            admin: 1,
            recruiter: 2,
            sales: 1,
            hr: 1
          },
          candidate_count: 5,
          recent_activities: [
            { id: 1, user_id: 1, activity_type: "LOGIN", description: "Admin logged in", timestamp: new Date().toISOString() }
          ],
          recent_candidates: [
            { id: 1, name: "John Doe", email: "john@example.com", job_title: "Developer", created_at: new Date().toISOString() }
          ]
        });
        
        setLoading(false);
      } catch (err) {
        setError('Failed to load dashboard data');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Sidebar />
        <div className="flex justify-center items-center flex-grow">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen">
        <Sidebar />
        <div className="flex justify-center items-center flex-grow">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Sidebar />
      <div className="container mx-auto p-6 flex-grow">
        <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">User Statistics</h2>
            <div className="space-y-2">
              <p><span className="font-medium">Total Admin:</span> {dashboardData?.user_stats?.admin || 0}</p>
              <p><span className="font-medium">Total Recruiters:</span> {dashboardData?.user_stats?.recruiter || 0}</p>
              <p><span className="font-medium">Total Sales:</span> {dashboardData?.user_stats?.sales || 0}</p>
              <p><span className="font-medium">Total HR:</span> {dashboardData?.user_stats?.hr || 0}</p>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Candidate Statistics</h2>
            <p><span className="font-medium">Total Candidates:</span> {dashboardData?.candidate_count || 0}</p>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-lg font-semibold mb-4">Recent Activities</h2>
          {dashboardData?.recent_activities?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {dashboardData.recent_activities.map((activity) => (
                    <tr key={activity.id}>
                      <td className="px-6 py-4 whitespace-nowrap">User #{activity.user_id}</td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{activity.activity_type}</div>
                        <div className="text-sm text-gray-500">{activity.description}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(activity.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">No recent activities</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;