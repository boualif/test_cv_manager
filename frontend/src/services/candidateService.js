import api from './api';

const candidateService = {
  /**
   * Récupérer la liste des candidats
   */
  getCandidates: async () => {
    try {
      const response = await api.get('/candidates/');
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des candidats:', error);
      throw error;
    }
  },

  /**
   * Récupérer un candidat par son ID avec les informations sur qui l'a importé
   */
  getCandidateWithUploader: async (candidateId) => {
    try {
      const response = await api.get(`/candidates/with-uploader/${candidateId}`);
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la récupération du candidat ${candidateId}:`, error);
      throw error;
    }
  },

  /**
   * Obtenir le CV du candidat
   */
  getCandidateResume: async (candidateId) => {
    try {
      const response = await api.get(`/candidates/${candidateId}/resume`, {
        responseType: 'blob' // Important pour les fichiers PDF
      });
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la récupération du CV du candidat ${candidateId}:`, error);
      throw error;
    }
  },
  /**
   * Mettre à jour les informations d'un candidat
   */
  updateCandidate: async (candidateId, candidateData) => {
    try {
      const response = await api.put(`/candidates/${candidateId}`, candidateData);
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la mise à jour du candidat ${candidateId}:`, error);
      throw error;
    }
  },

  /**
   * Mettre à jour une section spécifique du CV d'un candidat
   */
  updateCandidateResume: async (candidateId, sectionData) => {
    try {
      const response = await api.put(`/candidates/${candidateId}/resume`, sectionData);
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la mise à jour du CV du candidat ${candidateId}:`, error);
      throw error;
    }
  },

  /**
   * Supprimer un candidat
   */
  deleteCandidate: async (candidateId) => {
    try {
      await api.delete(`/candidates/${candidateId}`);
      return true;
    } catch (error) {
      console.error(`Erreur lors de la suppression du candidat ${candidateId}:`, error);
      throw error;
    }
  },

  /**
   * Télécharger un CV
   */
  uploadCV: async (fileContents) => {
    try {
      const response = await api.post('/candidates/cv/add', {
        fileContents
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors du téléchargement du CV:', error);
      throw error;
    }
  }
};

export default candidateService;