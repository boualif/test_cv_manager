import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';

const UploadCV = () => {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Vérifier si un token est présent (pour le débogage)
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        console.log('Token présent:', !!user.access_token);
      } catch (e) {
        console.error('Erreur lors du parsing de l\'utilisateur depuis localStorage:', e);
      }
    } else {
      console.log('Aucun utilisateur dans localStorage');
    }

    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/candidates/');
      setCandidates(response.data);
      setError('');
    } catch (error) {
      console.error('Error fetching candidates:', error);
      
      // Si l'erreur est 401, rediriger vers la page de connexion
      if (error.response && error.response.status === 401) {
        setError('Votre session a expiré. Redirection vers la page de connexion...');
        setTimeout(() => {
          navigate('/login', { state: { from: window.location.pathname } });
        }, 2000);
      } else {
        // Gérer d'autres erreurs
        setError(`Erreur lors de la récupération des candidats: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    Promise.all(selectedFiles.map(file => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(file);
      });
    })).then(base64Files => {
      setFiles(base64Files);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (files.length === 0) {
      setMessage('Veuillez sélectionner au moins un fichier');
      return;
    }
    
    try {
      setLoading(true);
      const response = await api.post('/candidates/cv/add', {
        fileContents: files
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      setMessage(`Succès: ${response.data.success.length} CVs téléchargés, ${response.data.duplicates.length} doublons, ${response.data.error_count} erreurs`);
      fetchCandidates(); // Rafraîchir la liste des candidats
    } catch (error) {
      console.error("Upload error:", error);
      
      // Si l'erreur est 401, rediriger vers la page de connexion
      if (error.response && error.response.status === 401) {
        setMessage('Votre session a expiré. Redirection vers la page de connexion...');
        setTimeout(() => {
          navigate('/login', { state: { from: window.location.pathname } });
        }, 2000);
      } else {
        // Gérer d'autres erreurs
        setMessage(`Erreur lors du téléchargement des CVs: ${error.message || 'Erreur inconnue'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto md:ml-64 p-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Télécharger des CVs</h1>
          
          {/* Afficher un message concernant l'utilisateur connecté */}
          {currentUser && (
            <p className="mb-4 text-gray-600">
              Connecté en tant que: {currentUser.username} ({currentUser.role})
            </p>
          )}
          
          {/* Affichage des erreurs */}
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <p>{error}</p>
            </div>
          )}
          
          {/* Formulaire de téléchargement */}
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="file"
                accept=".pdf"
                multiple
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                disabled={loading}
              />
              <button
                type="submit"
                className={`bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={loading}
              >
                {loading ? 'Traitement en cours...' : 'Télécharger'}
              </button>
            </form>
            
            {message && (
              <div className={`mt-4 p-3 rounded ${message.includes('Erreur') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                {message}
              </div>
            )}
          </div>

          {/* Liste des candidats */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-bold mb-4">Candidats téléchargés</h2>
            
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            ) : candidates.length === 0 ? (
              <p className="text-gray-500 py-4">Aucun candidat téléchargé pour le moment</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {candidates.map((candidate) => (
                  <div key={candidate.id} className="bg-gray-50 p-4 rounded shadow border border-gray-200">
                    <h3 className="font-bold">{candidate.name}</h3>
                    <p className="text-gray-600">{candidate.job_title}</p>
                    <p className="text-sm text-gray-500">{candidate.email}</p>
                    <Link 
                      to={`/candidates/${candidate.id}`}
                      className="mt-2 text-blue-500 hover:underline block"
                    >
                      Voir le profil
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadCV;