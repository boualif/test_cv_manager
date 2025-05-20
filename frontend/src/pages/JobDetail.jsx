import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import jobService from '../services/jobService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const JobDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchJobDetails();
  }, [id]);

  const fetchJobDetails = async () => {
    try {
      setLoading(true);
      const data = await jobService.getJob(id);
      setJob(data);
      setError('');
      if (data.is_demo) {
        toast.info("Cette offre d'emploi est en mode démonstration.");
      }
    } catch (error) {
      console.error("Erreur lors du chargement des détails de l'offre d'emploi:", error);
      setError("Impossible de charger les détails de l'offre d'emploi");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteJob = async () => {
    try {
      setIsSaving(true);
      await jobService.deleteJob(id);
      toast.success("Offre d'emploi supprimée avec succès");
      setTimeout(() => navigate('/jobs'), 1500);
    } catch (error) {
      console.error("Erreur lors de la suppression de l'offre d'emploi:", error);
      toast.error("Erreur lors de la suppression de l'offre d'emploi");
    } finally {
      setIsSaving(false);
      setShowDeleteModal(false);
    }
  };

  const getJobTypeLabel = (type) => {
    if (!type || type === 'Non spécifié') {
      return <span className="px-3 py-1 rounded-full text-sm"><span className="bg-gray-200 text-gray-800 font-bold px-1 py-0.5 rounded-full">Non spécifié</span></span>;
    }
    switch (type.toLowerCase()) {
      case 'technique':
        return <span className="px-3 py-1 rounded-full text-sm"><span className="bg-blue-200 text-blue-800 font-bold px-1 py-0.5 rounded-full">Technique</span></span>;
      case 'fonctionnel':
        return <span className="px-3 py-1 rounded-full text-sm"><span className="bg-green-200 text-green-800 font-bold px-1 py-0.5 rounded-full">Fonctionnel</span></span>;
      case 'technico-fonctionnel':
      case 'technicofonctionnel':
        return <span className="px-3 py-1 rounded-full text-sm"><span className="bg-purple-200 text-purple-800 font-bold px-1 py-0.5 rounded-full">Technico-fonctionnel</span></span>;
      default:
        return <span className="px-3 py-1 rounded-full text-sm"><span className="bg-gray-200 text-gray-800 font-bold px-1 py-0.5 rounded-full">{type}</span></span>;
    }
  };

  const getJobTitle = (job) => {
  if (job.title && job.title !== 'Offre d’emploi') {
    return job.title;
  }
  if (job.details || job.description) {
    const text = job.details || job.description;
    const firstLine = text.split('\n')[0] || text;
    return firstLine.length > 50 ? firstLine.substring(0, 47) + '...' : firstLine;
  }
  return 'Offre d’emploi';
};

  const getCategorizedSkills = (job) => {
    // Use the new categorized skills if available
    const technicalSkills = job.technical_skills || [];
    const softSkills = job.soft_skills || [];
    const otherRequirements = job.other_requirements || [];
    
    // For backward compatibility, also include key_skills
    const keySkills = job.key_skills || [];
    
    // Merge technical skills and key skills, removing duplicates
    const allTechnicalSkills = [...new Set([...technicalSkills, ...keySkills])];
    
    return {
      technicalSkills: allTechnicalSkills,
      softSkills,
      otherRequirements
    };
  };

  const getContractDetails = (job) => {
    const contractType = job.contract_type || 'Non spécifié';
    const startDate = job.start_date || 'Non spécifié';
    const benefits = job.benefits || [];
    const workLocation = job.work_location || job.location || 'Non spécifié';
    const congésPayés = job.congés_payés || 'Non spécifié';
    const transportationBenefits = job.transportation_benefits || 'Non spécifié';
    const mealBenefits = job.meal_benefits || 'Non spécifié';
    
    return {
      contractType,
      startDate,
      benefits,
      workLocation,
      congésPayés,
      transportationBenefits,
      mealBenefits
    };
  };

  const highlightKeywords = (text) => {
    if (!text) return 'Aucun détail fourni.';

    const { technicalSkills, softSkills, otherRequirements } = getCategorizedSkills(job);
    const location = job.location || job.work_location ? [job.location || job.work_location] : [];
    const experience = job.experience_level ? [job.experience_level] : [];
    
    // Combine all keywords for highlighting
    const allKeywords = [...technicalSkills, ...softSkills, ...otherRequirements, ...location, ...experience];

    if (allKeywords.length === 0) return text;

    const escapedKeywords = allKeywords.map(keyword => keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const pattern = new RegExp(`\\b(${escapedKeywords.join('|')})\\b`, 'gi');

    const parts = text.split(pattern);
    return parts.map((part, index) => {
      // Check for matching keywords (case insensitive)
      const matchedKeyword = allKeywords.find(keyword => 
        keyword.toLowerCase() === part.toLowerCase()
      );
      
      if (matchedKeyword) {
        if (technicalSkills.some(skill => skill.toLowerCase() === part.toLowerCase())) {
          return <span key={index} className="bg-green-200 text-green-800 font-bold px-1 py-0.5 rounded-full">{part}</span>;
        } else if (softSkills.some(skill => skill.toLowerCase() === part.toLowerCase())) {
          return <span key={index} className="bg-yellow-200 text-yellow-800 font-bold px-1 py-0.5 rounded-full">{part}</span>;
        } else if (otherRequirements.some(req => req.toLowerCase() === part.toLowerCase())) {
          return <span key={index} className="bg-orange-200 text-orange-800 font-bold px-1 py-0.5 rounded-full">{part}</span>;
        } else if (location.some(loc => loc.toLowerCase() === part.toLowerCase())) {
          return <span key={index} className="bg-purple-200 text-purple-800 font-bold px-1 py-0.5 rounded-full">{part}</span>;
        } else if (experience.some(exp => exp.toLowerCase() === part.toLowerCase())) {
          return <span key={index} className="bg-blue-200 text-blue-800 font-bold px-1 py-0.5 rounded-full">{part}</span>;
        }
      }
      return part;
    });
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

  if (!job) {
    return (
      <div className="flex min-h-screen">
        <div className="w-64 flex-shrink-0">
          <Sidebar />
        </div>
        <div className="flex-1 flex justify-center items-center">
          <div className="text-gray-600">Offre d'emploi non trouvée</div>
        </div>
      </div>
    );
  }

  const { technicalSkills, softSkills, otherRequirements } = getCategorizedSkills(job);
  const contractDetails = getContractDetails(job);

  return (
    <div className="flex min-h-screen">
      <div className="w-64 flex-shrink-0">
        <Sidebar />
      </div>
      <div className="flex-1 p-6">
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

        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-800">
                  {job.is_demo && <span className="text-yellow-600">[Démo] </span>}
                  {getJobTitle(job)}
                </h1>
                <div className="flex flex-wrap gap-2 mt-2">
                  {getJobTypeLabel(job.job_type_etiquette)}
                  {job.competence_phare && job.competence_phare !== 'Non spécifié' && (
                    <span className="px-3 py-1 rounded-full text-sm"><span className="bg-yellow-200 text-yellow-800 font-bold px-1 py-0.5 rounded-full">{job.competence_phare}</span></span>
                  )}
                  {contractDetails.contractType && contractDetails.contractType !== 'Non spécifié' && (
                    <span className="px-3 py-1 rounded-full text-sm"><span className="bg-red-200 text-red-800 font-bold px-1 py-0.5 rounded-full">{contractDetails.contractType}</span></span>
                  )}
                </div>
              </div>
              <div className="mt-4 md:mt-0 flex space-x-2">
                <Link
                  to={`/jobs/${job.id}/edit`}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none flex items-center"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 mr-2"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
                    <path
                      fillRule="evenodd"
                      d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Modifier
                </Link>
                <Link
                  to={`/jobs/${job.id}/match`}
                  className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 focus:outline-none flex items-center"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 mr-2"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7zm-3 1a1 1 0 10-2 0v3a1 1 0 102 0V8zM8 9a1 1 0 00-2 0v2a1 1 0 102 0V9z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Analyser avec des candidats
                </Link>
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none flex items-center"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 mr-2"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Supprimer
                </button>
              </div>
            </div>
          </div>

          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Détails de l'offre</h2>
                <div className="bg-gray-50 p-4 rounded-lg whitespace-pre-line">
                  {highlightKeywords(job.details || job.description)}
                </div>
              </div>
              
              {/* Contract Details Section */}
              {(contractDetails.benefits && contractDetails.benefits.length > 0) && (
                <div>
                  <h2 className="text-lg font-semibold text-gray-800 mb-3">Avantages</h2>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <ul className="list-disc list-inside space-y-2">
                      {contractDetails.benefits.map((benefit, idx) => (
                        <li key={idx}>{benefit}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Informations</h2>
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Type de poste</dt>
                    <dd className="mt-1">{getJobTypeLabel(job.job_type_etiquette)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Compétence phare</dt>
                    <dd className="mt-1">
                      {job.competence_phare && job.competence_phare !== 'Non spécifié' ? (
                        <span className="bg-yellow-200 text-yellow-800 font-bold px-1 py-0.5 rounded-full">{job.competence_phare}</span>
                      ) : (
                        'Non spécifié'
                      )}
                    </dd>
                  </div>
                  
                  {/* Contract Type */}
                  {contractDetails.contractType && contractDetails.contractType !== 'Non spécifié' && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Type de contrat</dt>
                      <dd className="mt-1">
                        <span className="bg-red-200 text-red-800 font-bold px-1 py-0.5 rounded-full">
                          {contractDetails.contractType}
                        </span>
                      </dd>
                    </div>
                  )}
                  
                  {/* Start Date */}
                  {contractDetails.startDate && contractDetails.startDate !== 'Non spécifié' && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Date de début</dt>
                      <dd className="mt-1">{contractDetails.startDate}</dd>
                    </div>
                  )}
                  
                  {/* Technical Skills Section */}
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Compétences techniques</dt>
                    <dd className="mt-1">
                      {technicalSkills && technicalSkills.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {technicalSkills.map((skill, idx) => (
                            <span key={idx} className="bg-green-200 text-green-800 font-bold px-1 py-0.5 rounded-full">{skill}</span>
                          ))}
                        </div>
                      ) : (
                        'Non spécifié'
                      )}
                    </dd>
                  </div>
                  
                  {/* Soft Skills Section */}
                  {softSkills && softSkills.length > 0 && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Compétences comportementales</dt>
                      <dd className="mt-1">
                        <div className="flex flex-wrap gap-2">
                          {softSkills.map((skill, idx) => (
                            <span key={idx} className="bg-yellow-200 text-yellow-800 font-bold px-1 py-0.5 rounded-full">{skill}</span>
                          ))}
                        </div>
                      </dd>
                    </div>
                  )}
                  
                  {/* Other Requirements Section */}
                  {otherRequirements && otherRequirements.length > 0 && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Autres exigences</dt>
                      <dd className="mt-1">
                        <div className="flex flex-wrap gap-2">
                          {otherRequirements.map((req, idx) => (
                            <span key={idx} className="bg-orange-200 text-orange-800 font-bold px-1 py-0.5 rounded-full">{req}</span>
                          ))}
                        </div>
                      </dd>
                    </div>
                  )}
                  
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Niveau d'expérience</dt>
                    <dd className="mt-1">
                      {job.experience_level ? (
                        <span className="bg-blue-200 text-blue-800 font-bold px-1 py-0.5 rounded-full">{job.experience_level}</span>
                      ) : (
                        'Non spécifié'
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Localisation</dt>
                    <dd className="mt-1">
                      {contractDetails.workLocation && contractDetails.workLocation !== 'Non spécifié' ? (
                        <span className="bg-purple-200 text-purple-800 font-bold px-1 py-0.5 rounded-full">{contractDetails.workLocation}</span>
                      ) : (
                        'Non spécifié'
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Créé par</dt>
                    <dd className="mt-1">{job.created_by}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Date de création</dt>
                    <dd className="mt-1">
                      {new Date(job.created_at).toLocaleDateString()} à{' '}
                      {new Date(job.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </dd>
                  </div>
                  {job.updated_at && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Dernière modification</dt>
                      <dd className="mt-1">
                        {new Date(job.updated_at).toLocaleDateString()} à{' '}
                        {new Date(job.updated_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>
          </div>
        </div>

        {showDeleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h3 className="text-xl font-bold mb-4">Confirmer la suppression</h3>
              <p className="mb-6">
                Êtes-vous sûr de vouloir supprimer cette offre d'emploi ? Cette action est irréversible.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  disabled={isSaving}
                >
                  Annuler
                </button>
                <button
                  onClick={handleDeleteJob}
                  className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none"
                  disabled={isSaving}
                >
                  {isSaving ? 'Suppression...' : 'Supprimer'}
                </button>
              </div>
            </div>
          </div>
        )}

        <ToastContainer position="top-right" autoClose={3000} />
      </div>
    </div>
  );
};

export default JobDetail;