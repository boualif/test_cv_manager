import React, { useState, useEffect } from 'react';
import Header from '../../components/Header';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Sidebar from '../../components/Sidebar';

const UserManagement = () => {
  const { currentUser, loading: authLoading, error: authError, getUsers, createUser, deleteUser, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'recruiter',
  });

  useEffect(() => {
    console.log('UserManagement useEffect:', { currentUser, isAdmin, authLoading, authError });
    if (authLoading) return;

    if (!currentUser) {
      console.log('No currentUser, redirecting to /login');
      setError('You need to be logged in to access this page');
      setLoading(false);
      setTimeout(() => navigate('/login'), 3000);
      return;
    }

    if (!isAdmin) {
      console.log('Not admin, redirecting to /');
      setError('You need admin privileges to access this page');
      setLoading(false);
      setTimeout(() => navigate('/'), 3000);
      return;
    }

    fetchUsers();
  }, [currentUser, authLoading, isAdmin, navigate]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      console.log('Fetching users...');
      const usersData = await getUsers();
      console.log('Users fetched:', usersData);
      setUsers(usersData);
    } catch (err) {
      console.error('Fetch users error:', err.response || err);
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentUser) {
      alert('You need to be logged in to add users');
      return;
    }
    try {
      console.log('Creating user:', formData);
      await createUser(formData);
      console.log('User created, refreshing user list');
      await fetchUsers(); // Refresh the list from backend
      setIsModalOpen(false);
      setFormData({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'recruiter',
      });
    } catch (err) {
      console.error('Create user error:', err.response || err);
      alert(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleDelete = async (userId) => {
    if (!currentUser) {
      alert('You need to be logged in to delete users');
      return;
    }
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        console.log('Deleting user:', userId);
        await deleteUser(userId);
        console.log('User deleted:', userId);
        setUsers(users.filter((user) => user.id !== userId));
      } catch (err) {
        console.error('Delete user error:', err.response || err);
        alert(err.message || 'Failed to delete user');
      }
    }
  };

  if (loading || authLoading) {
    console.log('Rendering loading state');
    return (
      <div className="flex flex-col min-h-screen">
        <Sidebar />
        <div className="flex justify-center items-center flex-grow">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error || authError || !currentUser || !isAdmin) {
    console.log('Rendering error state:', { error, authError, currentUser, isAdmin });
    return (
      <div className="flex flex-col min-h-screen">
        <Sidebar />
        <div className="flex justify-center items-center flex-grow">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded max-w-md w-full" role="alert">
            <p className="font-bold">Error</p>
            <p>{error || authError || 'You need to be logged in as an admin to access this page'}</p>
            <div className="mt-4">
              <p className="font-medium">Please log in or contact an administrator.</p>
              <button
                onClick={() => navigate('/login')}
                className="mt-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
              >
                Go to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  console.log('Rendering UserManagement main content');
  return (
    <div className="flex flex-col min-h-screen">
      <Sidebar />
      <div className="container mx-auto p-6 flex-grow">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold">User Management</h1>
            <button
              onClick={fetchUsers}
              className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded inline-flex items-center"
            >
              <svg
                className="w-4 h-4 mr-2"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                  clipRule="evenodd"
                />
              </svg>
              Refresh
            </button>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md font-medium"
          >
            Add New User
          </button>
        </div>

        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Username
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Full Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{user.username}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">{user.full_name || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        user.role === 'admin'
                          ? 'bg-purple-100 text-purple-800'
                          : user.role === 'recruiter'
                          ? 'bg-blue-100 text-blue-800'
                          : user.role === 'sales'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 space-x-2">
                    <button
                      onClick={() => handleDelete(user.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {isModalOpen && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-10">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-medium text-gray-900">Add New User</h3>
              </div>
              <form onSubmit={handleSubmit}>
                <div className="px-6 py-4 space-y-4">
                  <div>
                    <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                      Username
                    </label>
                    <input
                      type="text"
                      id="username"
                      name="username"
                      value={formData.username}
                      onChange={handleInputChange}
                      required
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                      Email
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                      Password
                    </label>
                    <input
                      type="password"
                      id="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      required
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                      Full Name
                    </label>
                    <input
                      type="text"
                      id="full_name"
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleInputChange}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label htmlFor="role" className="block text-sm font-medium text-gray-700">
                      Role
                    </label>
                    <select
                      id="role"
                      name="role"
                      value={formData.role}
                      onChange={handleInputChange}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="admin">Admin</option>
                      <option value="recruiter">Recruiter</option>
                      <option value="sales">Sales</option>
                      <option value="hr">HR</option>
                    </select>
                  </div>
                </div>
                <div className="px-6 py-4 bg-gray-50 flex justify-end space-x-3 rounded-b-lg">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Create User
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;