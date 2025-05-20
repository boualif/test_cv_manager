import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',  // Ajout de /api à l'URL de base
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use((config) => {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return config;
    
    const user = JSON.parse(userStr);
    if (user && user.access_token) {
      config.headers.Authorization = `Bearer ${user.access_token}`;
    }
  } catch (error) {
    console.error('Erreur lors de la préparation de la requête:', error);
  }
  return config;
});

export default api;