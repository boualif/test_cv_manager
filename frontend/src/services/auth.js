// auth.js - Simplified for form-urlencoded only
import api from './api';
import axios from 'axios';

const login = async (username, password) => {
  try {
    console.log(`Attempting login for user: ${username}`);
    
    // FastAPI/OAuth2 standard format
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await axios.post(
      'http://localhost:8000/api/auth/token', 
      formData, 
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        withCredentials: false
      }
    );
    
    if (response.data.access_token) {
      // Store the complete user object for later use
      const userData = {
        access_token: response.data.access_token,
        user_id: response.data.user_id,
        username: response.data.username,
        role: response.data.role,
        token_type: response.data.token_type
      };
      
      localStorage.setItem('user', JSON.stringify(userData));
      console.log('Login successful, user data stored in localStorage');
      return response.data;
    }
    
    throw new Error('No access token received');
  } catch (error) {
    // Improved error handling - extract the message
    const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
    console.error('Login error:', errorMessage);
    throw error;
  }
};

const logout = () => {
  localStorage.removeItem('user');
  console.log('User logged out, localStorage cleared');
};

const getCurrentUser = () => {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.error('Error parsing user from localStorage:', error);
    localStorage.removeItem('user'); // Clear invalid data
    return null;
  }
};

const getUserProfile = async () => {
  try {
  const response = await api.get('/users/me');
  // Utilisez le chemin complet avec /api
    return response.data;
  } catch (error) {
    console.error('Error fetching user profile:', error.response?.data || error.message);
    throw error;
  }
};

const getUsers = async () => {
  try {
    const response = await api.get('/users');
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error.response?.data || error.message);
    throw error;
  }
};

const createUser = async (userData) => {
  try {
    const response = await api.post('/users', userData);
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error.response?.data || error.message);
    throw error;
  }
};

const deleteUser = async (userId) => {
  try {
    const response = await api.delete(`/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting user:', error.response?.data || error.message);
    throw error;
  }
};

const AuthService = {
  login,
  logout,
  getCurrentUser,
  getUserProfile,
  getUsers,
  createUser,
  deleteUser
};

export default AuthService;