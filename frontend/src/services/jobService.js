// Updated jobService.js with debugging
import api from './api';

// Helper function to parse array fields that might be stored as strings
const parseArrayField = (field) => {
  if (!field) return [];
  if (Array.isArray(field)) return field;
  if (typeof field === 'string') {
    try {
      const parsed = JSON.parse(field);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.warn(`Failed to parse ${field} as JSON`, e);
      return [];
    }
  }
  return [];
};

// Process all skills and benefits data for consistency
const processJobData = (job) => {
  if (!job) return job;
  
  // Add debugging to see the original job data
  console.log('Original job data:', job);
  
  // Process the job data
  const processedJob = {
    ...job,
    // Ensure description/details field consistency
    details: job.description || job.details,
    // Process all array fields that might come as strings
    technical_skills: parseArrayField(job.technical_skills),
    soft_skills: parseArrayField(job.soft_skills),
    other_requirements: parseArrayField(job.other_requirements),
    key_skills: parseArrayField(job.key_skills),
    benefits: parseArrayField(job.benefits),
    // Set demo flag
    is_demo: job.is_demo || false
  };
  
  // Add debugging to see the processed job data
  console.log('Processed job data:', processedJob);
  console.log('Technical skills:', processedJob.technical_skills);
  console.log('Soft skills:', processedJob.soft_skills);
  console.log('Other requirements:', processedJob.other_requirements);
  
  return processedJob;
};

const jobService = {
  getJobs: async () => {
    try {
      const response = await api.get('/jobs/');
      return response.data.map(job => processJobData(job));
    } catch (error) {
      console.error("Erreur lors de la récupération des offres d'emploi:", error);
      throw {
        message: error.response?.data?.detail || "Erreur lors de la récupération des offres d'emploi",
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  getJob: async (jobId) => {
    if (!jobId || isNaN(parseInt(jobId))) {
      throw new Error("ID de l'offre d'emploi invalide");
    }
    // Check localStorage for demo job first
    const demoJobs = JSON.parse(localStorage.getItem('demoJobs') || '{}');
    if (demoJobs[jobId]) {
      return processJobData({ ...demoJobs[jobId], is_demo: true });
    }
    try {
      console.log(`Fetching job with id ${jobId}...`);
      const response = await api.get(`/jobs/${jobId}`);
      console.log('Raw API response:', response.data);
      
      // Check if we have the skills data
      if (response.data) {
        console.log('Skills data in API response:');
        console.log('technical_skills:', response.data.technical_skills);
        console.log('soft_skills:', response.data.soft_skills);
        console.log('other_requirements:', response.data.other_requirements);
      }
      
      return processJobData({
        ...response.data,
        is_demo: false
      });
    } catch (error) {
      console.error(`Erreur lors de la récupération de l'offre d'emploi ${jobId}:`, error);
      throw {
        message: error.response?.data?.detail || `Erreur lors de la récupération de l'offre d'emploi ${jobId}`,
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  createJob: async (jobData) => {
    if (!jobData || typeof jobData !== 'object') {
      throw new Error("Données de l'offre d'emploi invalides");
    }
    if (!jobData.details || !jobData.details.trim()) {
      throw new Error("Le champ 'details' est requis et ne peut pas être vide");
    }
    try {
      const payload = { description: jobData.details.trim() };
      console.log('Payload sent to POST /jobs/auto:', payload);
      const response = await api.post('/jobs/auto', payload);
      console.log('Response from job creation:', response.data);
      return processJobData({
        ...response.data,
        is_demo: false
      });
    } catch (error) {
      console.error("Erreur lors de la création de l'offre d'emploi:", error);
      console.error("Response data:", error.response?.data);
      throw {
        message: error.response?.data?.detail || "Erreur lors de la création de l'offre d'emploi",
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  updateJob: async (jobId, jobData) => {
    if (!jobId || isNaN(parseInt(jobId))) {
      throw new Error("ID de l'offre d'emploi invalide");
    }
    if (!jobData || typeof jobData !== 'object') {
      throw new Error("Données de l'offre d'emploi invalides");
    }
    if (!jobData.details || !jobData.details.trim()) {
      throw new Error("Le champ 'details' est requis et ne peut pas être vide");
    }
    try {
      const payload = { description: jobData.details.trim() };
      console.log('Payload sent to PUT /jobs/:', payload);
      const response = await api.put(`/jobs/${jobId}`, payload);
      return processJobData({
        ...response.data,
        is_demo: false
      });
    } catch (error) {
      console.error(`Erreur lors de la mise à jour de l'offre d'emploi ${jobId}:`, error);
      console.error("Response data:", error.response?.data);
      throw {
        message: error.response?.data?.detail || `Erreur lors de la mise à jour de l'offre d'emploi ${jobId}`,
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  deleteJob: async (jobId) => {
    if (!jobId || isNaN(parseInt(jobId))) {
      throw new Error("ID de l'offre d'emploi invalide");
    }
    // Handle demo job deletion
    const demoJobs = JSON.parse(localStorage.getItem('demoJobs') || '{}');
    if (demoJobs[jobId]) {
      delete demoJobs[jobId];
      localStorage.setItem('demoJobs', JSON.stringify(demoJobs));
      return true;
    }
    try {
      await api.delete(`/jobs/${jobId}`);
      return true;
    } catch (error) {
      console.error(`Erreur lors de la suppression de l'offre d'emploi ${jobId}:`, error);
      throw {
        message: error.response?.data?.detail || `Erreur lors de la suppression de l'offre d'emploi ${jobId}`,
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  getCandidates: async () => {
    try {
      const response = await api.get('/candidates/');
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des candidats:', error);
      throw {
        message: error.response?.data?.detail || 'Erreur lors de la récupération des candidats',
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  analyzeJobMatch: async (jobId, candidateIds) => {
    if (!jobId || isNaN(parseInt(jobId))) {
      throw new Error('jobId est requis et doit être un nombre');
    }
    if (!Array.isArray(candidateIds) || candidateIds.length === 0) {
      throw new Error('candidateIds doit être un tableau non vide');
    }
    const numJobId = parseInt(jobId, 10);
    const numericCandidateIds = candidateIds.map(id => {
      const numId = parseInt(id, 10);
      if (isNaN(numId)) {
        throw new Error(`ID de candidat invalide: ${id}`);
      }
      return numId;
    });
    try {
      const requestData = {
        job_id: numJobId,
        candidates: numericCandidateIds
      };
      const response = await api.post(`/jobs/${numJobId}/analyze-candidates`, requestData);
      return response.data.analyses || [];
    } catch (error) {
      console.error(`Erreur lors de l'analyse de correspondance pour l'offre ${numJobId}:`, error);
      throw {
        message: error.response?.data?.detail || 'Erreur lors de l\'analyse de correspondance',
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  suggestCandidatesForJob: async (jobId, options = {}) => {
    if (!jobId || isNaN(parseInt(jobId))) {
      throw new Error("ID de l'offre d'emploi invalide");
    }
    const { limit, minScore } = options;
    try {
      const queryParams = [];
      if (limit) queryParams.push(`limit=${limit}`);
      if (minScore) queryParams.push(`min_score=${minScore}`);
      const queryString = queryParams.length ? `?${queryParams.join('&')}` : '';
      const response = await api.post(`/jobs/${jobId}/suggest-candidates${queryString}`, {});
      return response.data;
    } catch (error) {
      console.error(`Erreur lors de la suggestion de candidats pour l'offre ${jobId}:`, error);
      throw {
        message: error.response?.data?.detail || 'Erreur lors de la suggestion de candidats',
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  },

  analyzeJobMatchAuto: async (jobId, options = {}) => {
    if (!jobId || isNaN(parseInt(jobId))) {
      throw new Error("ID de l'offre d'emploi invalide");
    }
    const { limit, minScore } = options;
    try {
      const queryParams = [];
      if (limit) queryParams.push(`limit=${limit}`);
      if (minScore) queryParams.push(`min_score=${minScore}`);
      const queryString = queryParams.length ? `?${queryParams.join('&')}` : '';
      const response = await api.post(`/jobs/${jobId}/analyze-auto${queryString}`, {});
      return response.data.analyses || [];
    } catch (error) {
      console.error(`Erreur lors de l'analyse automatique pour l'offre ${jobId}:`, error);
      throw {
        message: error.response?.data?.detail || 'Erreur lors de l\'analyse automatique',
        status: error.response?.status || 500,
        code: error.code || 'API_ERROR'
      };
    }
  }
};

export default jobService;