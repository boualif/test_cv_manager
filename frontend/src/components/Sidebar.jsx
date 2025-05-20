import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { currentUser, userRole, isAdmin, isRecruiter, isSales, isHR, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  
  // Détermine si un lien est actif
  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/') 
      ? 'bg-blue-700 text-white' 
      : 'text-blue-100 hover:bg-blue-700';
  };
// Add this function alongside the getRoleDashboardPath function
function getUploadPath() {
  if (isAdmin) return '/admin/upload';
  if (isRecruiter) return '/recruiter/upload';
  if (isSales) return '/sales/upload';
  if (isHR) return '/hr/upload';
  return '/upload'; // Default path
}
  // Sections qui apparaissent pour tous les utilisateurs
  const commonLinks = [
/*{
      title: 'Tableau de bord',
      path: getRoleDashboardPath(),
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2z" />
        </svg>
      )
    },*/
    {
      title: 'Candidats',
      path: '/candidates',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    },
    {
      title: 'Ajouter CV',
      path: getUploadPath(), // Using a function to determine the path based on role
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      )
    },
    {
      title: 'Offres d\'emploi',
      path: '/jobs',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      )
    }
  ];

  // Liens spécifiques pour les recruteurs
  const recruiterLinks = [
    {
      title: 'Entretiens',
      path: '/interviews',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    }
  ];

  // Liens spécifiques pour les administrateurs
  const adminLinks = [
    {
      title: 'Gestion des utilisateurs',
      path: '/admin/users',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      )
    },
  /*  {
      title: 'Paramètres',
      path: '/admin/settings',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },*/
    /*{
      title: 'Activité des utilisateurs',
      path: '/admin/activity',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      )
    }*/
  ];

  // Liens spécifiques pour les commerciaux
  const salesLinks = [
    {
      title: 'Opportunités',
      path: '/opportunities',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      )
    },
    {
      title: 'Prospects',
      path: '/prospects',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    }
  ];

  // Liens spécifiques pour les RH
  const hrLinks = [
    {
      title: 'Contrats',
      path: '/contracts',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    {
      title: 'Embauches',
      path: '/hires',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  ];

  // Fonction pour déterminer le chemin du tableau de bord en fonction du rôle
  function getRoleDashboardPath() {
    if (isAdmin) return '/admin/dashboard';
    if (isRecruiter) return '/recruiter/dashboard';
    if (isSales) return '/sales/dashboard';
    if (isHR) return '/hr/dashboard';
    return '/dashboard';
  }

  return (
    <>
      {/* Bouton mobile pour ouvrir/fermer la sidebar */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden fixed z-20 bottom-4 right-4 bg-blue-600 text-white p-2 rounded-full shadow-lg"
      >
        {isOpen ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {/* Sidebar */}
      <div className={`bg-gray-800 text-white w-64 min-h-screen py-7 px-2 fixed inset-y-0 left-0 transform transition duration-200 ease-in-out z-10 ${
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        <div className="flex items-center space-x-2 px-4 mb-8">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-2xl font-bold">AI Matching</span>
        </div>

        {/* Profil utilisateur */}
        <div className="mb-6 px-4">
          <div className="flex items-center space-x-3 bg-blue-900 rounded-lg p-3">
            <div className="bg-blue-700 h-10 w-10 rounded-full flex items-center justify-center text-xl font-semibold">
              {currentUser && currentUser.username ? currentUser.username.charAt(0).toUpperCase() : '?'}
            </div>
            <div>
              <p className="font-medium">{currentUser ? currentUser.username : 'Utilisateur'}</p>
              <p className="text-xs text-blue-300 capitalize">{userRole || 'Invité'}</p>
            </div>
          </div>
        </div>
        
        {/* Navigation principale */}
        <nav className="space-y-1">
          {/* Sections communes */}
          <div className="mb-4">
            <p className="px-4 text-xs text-blue-400 uppercase font-semibold mb-2">Principal</p>
            {commonLinks.map((link) => (
              <Link 
                key={link.path} 
                to={link.path} 
                className={`flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 ${isActive(link.path)}`}
                onClick={() => setIsOpen(false)}
              >
                {link.icon}
                <span>{link.title}</span>
              </Link>
            ))}
          </div>

          {/* Section recruteur */}
          {/*{(isRecruiter || isAdmin) && (
            <div className="mb-4">
              <p className="px-4 text-xs text-blue-400 uppercase font-semibold mb-2">Recrutement</p>
              {recruiterLinks.map((link) => (
                <Link 
                  key={link.path} 
                  to={link.path} 
                  className={`flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 ${isActive(link.path)}`}
                  onClick={() => setIsOpen(false)}
                >
                  {link.icon}
                  <span>{link.title}</span>
                </Link>
              ))}
            </div>
          )}*/}

          {/* Section commerciale */}
         {/* {(isSales || isAdmin) && (
            <div className="mb-4">
              <p className="px-4 text-xs text-blue-400 uppercase font-semibold mb-2">Commercial</p>
              {salesLinks.map((link) => (
                <Link 
                  key={link.path} 
                  to={link.path} 
                  className={`flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 ${isActive(link.path)}`}
                  onClick={() => setIsOpen(false)}
                >
                  {link.icon}
                  <span>{link.title}</span>
                </Link>
              ))}
            </div>
          )}*/}

          {/* Section RH */}
         {/* {(isHR || isAdmin) && (
            <div className="mb-4">
              <p className="px-4 text-xs text-blue-400 uppercase font-semibold mb-2">Ressources Humaines</p>
              {hrLinks.map((link) => (
                <Link 
                  key={link.path} 
                  to={link.path} 
                  className={`flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 ${isActive(link.path)}`}
                  onClick={() => setIsOpen(false)}
                >
                  {link.icon}
                  <span>{link.title}</span>
                </Link>
              ))}
            </div>
          )}

          {/* Section admin */}
          {isAdmin && (
            <div className="mb-4">
              <p className="px-4 text-xs text-blue-400 uppercase font-semibold mb-2">Administration</p>
              {adminLinks.map((link) => (
                <Link 
                  key={link.path} 
                  to={link.path} 
                  className={`flex items-center space-x-2 py-2.5 px-4 rounded transition duration-200 ${isActive(link.path)}`}
                  onClick={() => setIsOpen(false)}
                >
                  {link.icon}
                  <span>{link.title}</span>
                </Link>
              ))}
            </div>
          )}
        </nav>

        {/* Pied de la sidebar avec lien de déconnexion */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <button 
            className="flex items-center space-x-2 w-full py-2 px-4 rounded text-left text-blue-200 hover:bg-blue-700 transition duration-200"
            onClick={() => {
              if (window.confirm('Voulez-vous vraiment vous déconnecter ?')) {
                logout(); // Clear user session
                navigate('/login'); // Redirect to login page
              }
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Déconnexion</span>
          </button>
        </div>
      </div>
    </>
  );
};

export default Sidebar;