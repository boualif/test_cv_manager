// JobForm.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import jobService from '../services/jobService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const JobForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = !!id;

  const [jobDetails, setJobDetails] = useState('');
  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isEditing) {
      loadJob();
    }
  }, [id]);

  const loadJob = async () => {
    try {
      setLoading(true);
      const data = await jobService.getJob(id);
      const combinedDetails = [
        data.title || '',
        data.job_type_etiquette || '',
        data.competence_phare || '',
        data.details || data.description || ''
      ]
        .filter(Boolean)
        .join('\n\n');
      setJobDetails(combinedDetails);
      setError('');
      if (data.is_demo) {
        toast.info('Édition d’une offre en mode démo');
      }
    } catch (error) {
      console.error("Erreur lors du chargement de l'offre d'emploi:", error);
      setError("Impossible de charger les détails de l'offre d'emploi");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!jobDetails.trim()) {
      toast.error("Les détails de l'offre sont requis");
      return;
    }
    try {
      setSaving(true);
      const jobData = { details: jobDetails };
      let newJob;
      if (isEditing) {
        newJob = await jobService.updateJob(id, jobData);
        toast.success("Offre d'emploi mise à jour avec succès");
      } else {
        newJob = await jobService.createJob(jobData);
        toast.success("Offre d'emploi créée avec succès");
      }
      navigate(`/jobs/${newJob.id}`);
    } catch (error) {
      console.error("Erreur lors de l'enregistrement de l'offre d'emploi:", error);
      // Demo mode fallback
      const demoJobs = JSON.parse(localStorage.getItem('demoJobs') || '{}');
      const jobId = isEditing ? id : Math.floor(Math.random() * 1000) + 300;
      const fakeJob = {
        id: parseInt(jobId),
        title: jobDetails.split('\n')[0] || 'Offre d’emploi',
        details: jobDetails,
        description: jobDetails,
        created_at: new Date().toISOString(),
        created_by: 'Système (Mode démo)',
        is_demo: true
      };
      demoJobs[jobId] = fakeJob;
      localStorage.setItem('demoJobs', JSON.stringify(demoJobs));
      toast.info("Mode démo: Offre d'emploi sauvegardée localement");
      navigate(`/jobs/${jobId}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen">
        <div className="w-64 flex-shrink-0">
          <Sidebar />
        </div>
        <div className="flex-1 flex justify-center items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen">
        <div className="w-64 flex-shrink-0">
          <Sidebar />
        </div>
        <div className="flex-1 flex justify-center items-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">
            <p className="font-bold">Erreur</p>
            <p>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <div className="w-64 flex-shrink-0">
        <Sidebar />
      </div>
      <div className="flex-1 p-6">
        <div className="bg-white shadow-md rounded-lg p-6">
          <div className="mb-6">
            <Link to="/jobs" className="text-blue-500 hover:underline flex items-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 mr-2"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z"
                  clipRule="evenodd"
                />
              </svg>
              Retour à la liste des offres
            </Link>
          </div>

          <h1 className="text-2xl font-bold mb-6">
            {isEditing ? "Modifier l'offre d'emploi" : "Créer une offre d'emploi"}
          </h1>

          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-6">
              <div>
                <label htmlFor="jobDetails" className="block text-sm font-medium text-gray-700 mb-2">
                  Détails de l'offre *
                </label>
                <textarea
                  id="jobDetails"
                  name="jobDetails"
                  rows="12"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Entrez tous les détails de l'offre : titre, type de poste (technique, fonctionnel, technico-fonctionnel), compétence phare, description, responsabilités, exigences, etc."
                  value={jobDetails}
                  onChange={(e) => setJobDetails(e.target.value)}
                ></textarea>
                <p className="text-xs text-gray-500 mt-1">
                  Fournissez une description complète pour une meilleure extraction automatique (titre, compétence phare, type de poste).
                </p>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <Link
                  to="/jobs"
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Annuler
                </Link>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none"
                  disabled={saving}
                >
                  {saving ? (
                    <span className="flex items-center">
                      <svg
                        className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      Enregistrement...
                    </span>
                  ) : (
                    isEditing ? "Enregistrer les modifications" : "Créer l'offre d'emploi"
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>

        <ToastContainer position="top-right" autoClose={3000} />
      </div>
    </div>
  );
};

export default JobForm;