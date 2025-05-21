import React, { createContext, useState, useEffect, useContext } from 'react';
import { jwtDecode } from 'jwt-decode';
import AuthService from '../services/auth';
import api from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const user = AuthService.getCurrentUser();

        if (user && user.access_token) {
          try {
            const decoded = jwtDecode(user.access_token);
            const now = Math.floor(Date.now() / 1000);

            if (decoded.exp && decoded.exp < now) {
              console.warn('Token expired, logging out user');
              AuthService.logout();
              setError('Session expired. Please login again.');
              setLoading(false);
              return;
            }

            setUserRole(decoded.role.toLowerCase());
            try {
              const profile = await AuthService.getUserProfile();
              setCurrentUser(profile);
            } catch (profileError) {
              setCurrentUser({
                username: decoded.sub,
                role: decoded.role.toLowerCase()
              });
            }
          } catch (err) {
            console.error('Token validation error:', err);
            AuthService.logout();
            setCurrentUser(null);
            setUserRole(null);
            setError('Session invalid. Please login again.');
          }
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (username, password) => {
    try {
      setError(null);
      const response = await AuthService.login(username, password);
      
      if (response.access_token) {
        const decoded = jwtDecode(response.access_token);
        setUserRole(decoded.role.toLowerCase());
        const profile = await AuthService.getUserProfile();
        setCurrentUser(profile);
        return profile;
      } else {
        throw new Error("No token received");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError('Login failed. Please check your credentials.');
      throw err;
    }
  };

  const logout = () => {
    AuthService.logout();
    setCurrentUser(null);
    setUserRole(null);
  };

  const getUsers = async () => {
    try {
      setError(null);
      const response = await api.get('/users');
      return response.data;
    } catch (err) {
      setError('Failed to fetch users.');
      throw err;
    }
  };

  const createUser = async (userData) => {
    try {
      setError(null);
      const response = await api.post('/users/', userData);
      return response.data;
    } catch (err) {
      console.error('Failed to create user:', err);
      let errorMessage = 'Failed to create user.';
      if (err.response && err.response.data && err.response.data.detail) {
        if (Array.isArray(err.response.data.detail)) {
          const validationErrors = err.response.data.detail.map(error => error.msg).join(', ');
          errorMessage = validationErrors;
        } else {
          errorMessage = err.response.data.detail;
        }
      }
      setError(errorMessage);
      throw err;
    }
  };
    
  const deleteUser = async (userId) => {
    try {
      setError(null);
      await api.delete(`/users/${userId}`);
    } catch (err) {
      setError('Failed to delete user.');
      throw err;
    }
  };

  const value = {
    currentUser,
    userRole,
    loading,
    error,
    login,
    logout,
    getUsers,
    createUser,
    deleteUser,
    isAdmin: userRole === 'admin',
    isRecruiter: userRole === 'recruiter',
    isSales: userRole === 'sales',
    isHR: userRole === 'hr',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};
