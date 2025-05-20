import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const { currentUser, logout, isAdmin, isRecruiter, isSales, isHR } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="text-xl font-bold text-blue-600">CV Manager</Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:items-center space-x-4">
              {isAdmin && (
                <>
                  <Link to="/admin/dashboard" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                    Admin Dashboard
                  </Link>
                  <Link to="/admin/users" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                    User Management
                  </Link>
                  <Link to="/admin/upload" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                    Upload CV
                  </Link>
                  <Link to="/candidates" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                   Candidate List
                  </Link>

                  
                </>
              )}
              
              {isRecruiter && (
                <>
                  <Link to="/recruiter/dashboard" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                    Recruiter Dashboard
                  </Link>
                  <Link to="/upload" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                    Upload CV
                  </Link>
                </>
              )}
              
              {isSales && (
                <Link to="/sales/dashboard" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                  Sales Dashboard
                </Link>
              )}
              
              {isHR && (
                <Link to="/hr/dashboard" className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                  HR Dashboard
                </Link>
              )}
            </div>
          </div>
          
          <div className="flex items-center">
            <div className="ml-3 relative">
              <div>
                <button
                  type="button"
                  className="bg-white rounded-full flex text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  id="user-menu"
                  aria-expanded="false"
                  aria-haspopup="true"
                  onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                >
                  <span className="sr-only">Open user menu</span>
                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-800 font-medium">
                      {currentUser?.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                </button>
              </div>
              
              {isProfileMenuOpen && (
                <div
                  className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                  role="menu"
                  aria-orientation="vertical"
                  aria-labelledby="user-menu"
                >
                  <div className="px-4 py-2 text-xs text-gray-500">
                    Logged in as <span className="font-medium">{currentUser?.username}</span>
                  </div>
                  <div className="border-t border-gray-100"></div>
                  
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    role="menuitem"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;