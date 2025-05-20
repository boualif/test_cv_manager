import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import PDFViewer from '../components/PDFViewer';
import Sidebar from '../components/Sidebar';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const CandidateProfile = () => {
  const { id } = useParams();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('basic');
  const [contractStatus, setContractStatus] = useState('pending');
  const [contractStartDate, setContractStartDate] = useState('');
  const [contractEndDate, setContractEndDate] = useState('');
  const [contractType, setContractType] = useState('CDI');
  const [contractSalary, setContractSalary] = useState('');
  const [contractNotes, setContractNotes] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  // Nouveaux états pour l'édition
  const [isEditing, setIsEditing] = useState({
    personalInfo: false,
    hardSkills: false,
    softSkills: false
  });
  const [editValues, setEditValues] = useState({
    personalInfo: {
      name: '',
      email: '',
      job_title: '',
      phone: '',
      country: '',
      linkedin: '',
      github: ''
    },
    hardSkills: [],
    softSkills: [],
    newSkill: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  // Ajouter après l'effet qui charge les données du candidat
  useEffect(() => {
    if (candidate) {
      const candidateInfo = candidate.resume_data?.CandidateInfo || {};
      setEditValues({
        personalInfo: {
          name: candidateInfo.FullName || candidate.candidate.name,
          email: candidateInfo.Email || candidate.candidate.email,
          job_title: candidateInfo.CurrentJobTitle || candidate.candidate.job_title,
          phone: candidateInfo.PhoneNumber?.FormattedNumber || '',
          country: candidateInfo.Country || '',
          linkedin: candidateInfo.Linkedin || '',
          github: candidateInfo.Github || ''
        },
        hardSkills: candidate.resume_data?.HardSkills || [],
        softSkills: candidate.resume_data?.SoftSkills || [],
        newSkill: ''
      });
    }
  }, [candidate]);
  // Basculer le mode d'édition pour une section
  const toggleEdit = (section) => {
    // Réinitialiser d'abord toutes les sections en mode non-édition
    const newIsEditing = { personalInfo: false, hardSkills: false, softSkills: false };
    
    // Activer le mode d'édition pour la section spécifiée
    newIsEditing[section] = !isEditing[section];
    setIsEditing(newIsEditing);
    
    // Si on active le mode d'édition, initialiser les valeurs
    if (!isEditing[section]) {
      if (section === 'personalInfo') {
        const candidateInfo = candidate.resume_data?.CandidateInfo || {};
        setEditValues({
          ...editValues,
          personalInfo: {
            name: candidateInfo.FullName || candidate.candidate.name,
            email: candidateInfo.Email || candidate.candidate.email,
            job_title: candidateInfo.CurrentJobTitle || candidate.candidate.job_title,
            phone: candidateInfo.PhoneNumber?.FormattedNumber || '',
            country: candidateInfo.Country || '',
            linkedin: candidateInfo.Linkedin || '',
            github: candidateInfo.Github || ''
          }
        });
      } else if (section === 'hardSkills') {
        setEditValues({
          ...editValues,
          hardSkills: candidate.resume_data?.HardSkills || [],
          newSkill: ''
        });
      } else if (section === 'softSkills') {
        setEditValues({
          ...editValues,
          softSkills: candidate.resume_data?.SoftSkills || [],
          newSkill: ''
        });
      }
    }
  };

  // Gérer les changements dans les champs du formulaire
  const handleInputChange = (e, section) => {
    const { name, value } = e.target;
    
    if (section === 'personalInfo') {
      setEditValues({
        ...editValues,
        personalInfo: {
          ...editValues.personalInfo,
          [name]: value
        }
      });
    } else {
      setEditValues({
        ...editValues,
        [name]: value
      });
    }
  };

  // Ajouter une compétence
  const addSkill = (skillType) => {
    if (editValues.newSkill.trim() === '') return;
    
    if (skillType === 'hard') {
      setEditValues({
        ...editValues,
        hardSkills: [...editValues.hardSkills, editValues.newSkill],
        newSkill: ''
      });
    } else {
      setEditValues({
        ...editValues,
        softSkills: [...editValues.softSkills, editValues.newSkill],
        newSkill: ''
      });
    }
  };

  // Supprimer une compétence
  const removeSkill = (skillType, index) => {
    if (skillType === 'hard') {
      const newSkills = [...editValues.hardSkills];
      newSkills.splice(index, 1);
      setEditValues({
        ...editValues,
        hardSkills: newSkills
      });
    } else {
      const newSkills = [...editValues.softSkills];
      newSkills.splice(index, 1);
      setEditValues({
        ...editValues,
        softSkills: newSkills
      });
    }
  };

  // Enregistrer les informations personnelles
  const savePersonalInfo = async () => {
    try {
      setIsSaving(true);
      
      // Mettre à jour les informations de base du candidat
      await api.put(`/candidates/${id}`, {
        name: editValues.personalInfo.name,
        email: editValues.personalInfo.email,
        job_title: editValues.personalInfo.job_title
      });
      
      // Mettre à jour les données du CV
      const updatedCandidateInfo = {
        ...candidate.resume_data.CandidateInfo,
        FullName: editValues.personalInfo.name,
        Email: editValues.personalInfo.email,
        CurrentJobTitle: editValues.personalInfo.job_title,
        Country: editValues.personalInfo.country,
        Linkedin: editValues.personalInfo.linkedin,
        Github: editValues.personalInfo.github
      };
      
      // Mettre à jour le téléphone si fourni
      if (editValues.personalInfo.phone) {
        updatedCandidateInfo.PhoneNumber = {
          ...(candidate.resume_data.CandidateInfo.PhoneNumber || {}),
          FormattedNumber: editValues.personalInfo.phone
        };
      }
      
      await api.put(`/candidates/${id}/resume`, {
        section: 'CandidateInfo',
        data: updatedCandidateInfo
      });
      
      // Mettre à jour l'état local
      setCandidate({
        ...candidate,
        candidate: {
          ...candidate.candidate,
          name: editValues.personalInfo.name,
          email: editValues.personalInfo.email,
          job_title: editValues.personalInfo.job_title
        },
        resume_data: {
          ...candidate.resume_data,
          CandidateInfo: updatedCandidateInfo
        }
      });
      
      toast.success('Informations personnelles mises à jour avec succès');
      toggleEdit('personalInfo');
    } catch (error) {
      console.error('Error saving personal info:', error);
      toast.error('Erreur lors de la mise à jour des informations');
    } finally {
      setIsSaving(false);
    }
  };

  // Enregistrer les compétences
  const saveSkills = async (skillType) => {
    try {
      setIsSaving(true);
      
      const sectionName = skillType === 'hard' ? 'HardSkills' : 'SoftSkills';
      const skills = skillType === 'hard' ? editValues.hardSkills : editValues.softSkills;
      
      await api.put(`/candidates/${id}/resume`, {
        section: sectionName,
        data: skills
      });
      
      // Mettre à jour l'état local
      setCandidate({
        ...candidate,
        resume_data: {
          ...candidate.resume_data,
          [sectionName]: skills
        }
      });
      
      toast.success('Compétences mises à jour avec succès');
      toggleEdit(skillType === 'hard' ? 'hardSkills' : 'softSkills');
    } catch (error) {
      console.error('Error saving skills:', error);
      toast.error('Erreur lors de la mise à jour des compétences');
    } finally {
      setIsSaving(false);
    }
  };

  // Supprimer un candidat
  const handleDeleteCandidate = async () => {
    try {
      setIsSaving(true);
      await api.delete(`/candidates/${id}`);
      toast.success('Candidat supprimé avec succès');
      navigate('/candidates');
    } catch (error) {
      console.error('Error deleting candidate:', error);
      toast.error('Erreur lors de la suppression du candidat');
    } finally {
      setIsSaving(false);
      setShowDeleteModal(false);
    }
  };
  // État pour gérer les sections ouvertes dans la fiche candidat
  const [expandedSections, setExpandedSections] = useState({
    personal: true,
    experience: true,
    education: true,
    skills: true,
    projects: false // Projects fermé par défaut car peut être volumineux
  });

  // Toggle pour ouvrir/fermer les sections
  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section]
    });
  };

  useEffect(() => {
    const fetchCandidate = async () => {
      try {
        const response = await api.get(`/candidates/candidates/with-uploader/${id}`);
        setCandidate(response.data);
        
        // Si des données de contrat existent dans la réponse, les initialiser ici
        if (response.data.contract) {
          setContractStatus(response.data.contract.status || 'pending');
          setContractStartDate(response.data.contract.startDate || '');
          setContractEndDate(response.data.contract.endDate || '');
          setContractType(response.data.contract.type || 'CDI');
          setContractSalary(response.data.contract.salary || '');
          setContractNotes(response.data.contract.notes || '');
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching candidate:', error);
        
        if (error.response && error.response.status === 401) {
          setError('Votre session a expiré. Redirection vers la page de connexion...');
          setTimeout(() => {
            navigate('/login', { state: { from: window.location.pathname } });
          }, 2000);
        } else {
          setError('Erreur lors du chargement des données du candidat');
        }
        setLoading(false);
      }
    };

    fetchCandidate();
  }, [id, navigate]);

  const handlePdfDownload = async (e) => {
    e.preventDefault();
    try {
      const response = await api.get(`/candidates/${id}/resume`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `candidate_${id}_resume.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading resume:', error);
      
      if (error.response && error.response.status === 401) {
        setError('Votre session a expiré. Redirection vers la page de connexion...');
        setTimeout(() => {
          navigate('/login', { state: { from: window.location.pathname } });
        }, 2000);
      } else {
        setError(`Erreur lors du téléchargement du CV: ${error.message}`);
      }
    }
  };

  const handleContractSubmit = async (e) => {
    e.preventDefault();
    setSaveMessage('');
    
    try {
      // Simule une mise à jour du contrat - remplacer par un vrai appel API dans votre implémentation
      // const response = await api.post(`/candidates/${id}/contract`, {
      //   status: contractStatus,
      //   startDate: contractStartDate,
      //   endDate: contractEndDate,
      //   type: contractType,
      //   salary: contractSalary,
      //   notes: contractNotes
      // });
      
      // Affiche un message de succès
      setSaveMessage('Les informations du contrat ont été enregistrées avec succès.');
      
      // Simule une réponse réussie
      console.log('Contract updated successfully', {
        status: contractStatus,
        startDate: contractStartDate,
        endDate: contractEndDate,
        type: contractType,
        salary: contractSalary,
        notes: contractNotes
      });
      
      // Reset le message après 3 secondes
      setTimeout(() => {
        setSaveMessage('');
      }, 3000);
      
    } catch (error) {
      console.error('Error updating contract:', error);
      setSaveMessage('Erreur lors de la mise à jour du contrat.');
    }
  };
  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Sidebar />
        <div className="flex justify-center items-center flex-grow">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen">
        <Sidebar />
        <div className="flex justify-center items-center flex-grow">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded" role="alert">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        </div>
      </div>
    );
  }
  if (loading) return <div className="text-center p-8">Chargement en cours...</div>;
  if (error) return <div className="text-center p-8 text-red-500">{error}</div>;
  if (!candidate) return <div className="text-center p-8">Candidat non trouvé</div>;

  const candidateInfo = candidate.resume_data?.CandidateInfo || {};
  const experiences = candidate.resume_data?.ProfessionalExperience || [];
  const degrees = candidate.resume_data?.Degrees || [];
  const certifications = candidate.resume_data?.Certifications || [];
  const hardSkills = candidate.resume_data?.HardSkills || [];
  const softSkills = candidate.resume_data?.SoftSkills || [];
  const projects = candidate.resume_data?.Projects || [];
  const suggestedJobs = candidate.resume_data?.SuggestedJobs || [];

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Sidebar />
      <div className="md:ml-64 flex-grow px-4 py-6">
        <div className="container mx-auto">
          <Link to="/dashboard" className="text-blue-500 hover:underline flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Retour au Tableau de Bord
          </Link>
        </div>

        <div className="bg-white shadow-md rounded-lg overflow-hidden mb-6">
          {/* En-tête du profil avec photo et actions */}
          <div className="p-6 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
              <div className="flex items-center mb-4 md:mb-0">
                {/* Placeholder pour photo de profil - remplacer par une vraie photo si disponible */}
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-blue-500 text-xl font-bold mr-4">
                  {candidate.candidate.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-800">{candidate.candidate.name}</h1>
                  <p className="text-lg text-gray-600">{candidateInfo.CurrentJobTitle || candidate.candidate.job_title}</p>
                </div>
              </div>
              <div className="flex space-x-3">
                <button 
                  onClick={handlePdfDownload}
                  className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded flex items-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  Télécharger CV
                </button>
                <button className="bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                  </svg>
                  Contacter
                </button>
              </div>
            </div>
          </div>

          {/* Navigation par onglets */}
          <div className="bg-gray-100 border-b">
            <div className="container mx-auto">
              <div className="flex overflow-x-auto">
                <button 
                  className={`py-3 px-6 font-medium text-sm focus:outline-none ${activeTab === 'basic' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                  onClick={() => setActiveTab('basic')}
                >
                  Fiche Candidat
                </button>
                <button 
                  className={`py-3 px-6 font-medium text-sm focus:outline-none ${activeTab === 'contract' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                  onClick={() => setActiveTab('contract')}
                >
                  Gestion de Contrat
                </button>
                <button 
                  className={`py-3 px-6 font-medium text-sm focus:outline-none ${activeTab === 'resume' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                  onClick={() => setActiveTab('resume')}
                >
                  CV PDF
                </button>
              </div>
            </div>
          </div>

          {/* Contenu de l'onglet actif */}
          <div className="p-6">
            {/* Onglet Fiche Candidat - Toutes les informations en une seule page */}
            {activeTab === 'basic' && (
              <div className="space-y-8">
                {/* 1. Section Informations Personnelles */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-blue-50 p-4 border-b border-gray-200 flex justify-between items-center cursor-pointer">
                    <h2 
                      className="text-lg font-semibold text-gray-800" 
                      onClick={() => toggleSection('personal')}
                    >
                      Informations Personnelles
                    </h2>
                    <div className="flex items-center">
                      {!isEditing.personalInfo && (
                        <button 
                          className="mr-3 text-blue-500 hover:text-blue-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleEdit('personalInfo');
                          }}
                          title="Modifier"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                          </svg>
                        </button>
                      )}
                      <button 
                        className="text-gray-500 hover:text-gray-700"
                        onClick={() => toggleSection('personal')}
                      >
                        {expandedSections.personal ? (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                  
                  {expandedSections.personal && (
                    <div className="divide-y divide-gray-200">
                      {!isEditing.personalInfo ? (
                        // Mode affichage
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4">
                          <div className="p-4 border-r border-gray-200">
                            <table className="w-full text-sm">
                              <tbody>
                                <tr className="bg-gray-50">
                                  <td className="py-2 px-3 font-medium text-gray-500">Nom complet</td>
                                  <td className="py-2 px-3">{candidateInfo.FullName || candidate.candidate.name}</td>
                                </tr>
                                <tr>
                                  <td className="py-2 px-3 font-medium text-gray-500">Email</td>
                                  <td className="py-2 px-3">{candidateInfo.Email || candidate.candidate.email}</td>
                                </tr>
                                <tr className="bg-gray-50">
                                  <td className="py-2 px-3 font-medium text-gray-500">Titre du poste</td>
                                  <td className="py-2 px-3">{candidateInfo.CurrentJobTitle || candidate.candidate.job_title}</td>
                                </tr>
                                {candidateInfo.PhoneNumber && candidateInfo.PhoneNumber.FormattedNumber && (
                                  <tr>
                                    <td className="py-2 px-3 font-medium text-gray-500">Téléphone</td>
                                    <td className="py-2 px-3">{candidateInfo.PhoneNumber.FormattedNumber}</td>
                                  </tr>
                                )}
                                {candidateInfo.Country && (
                                  <tr className="bg-gray-50">
                                    <td className="py-2 px-3 font-medium text-gray-500">Pays</td>
                                    <td className="py-2 px-3">{candidateInfo.Country}</td>
                                  </tr>
                                )}
                                {candidateInfo.Languages && candidateInfo.Languages.length > 0 && (
                                  <tr>
                                    <td className="py-2 px-3 font-medium text-gray-500">Langues</td>
                                    <td className="py-2 px-3">{candidateInfo.Languages.join(', ')}</td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                          
                          <div className="p-4">
                            {/* Le reste de l'affichage existant */}
                          </div>
                        </div>
                      ) : (
                        // Mode édition
                        <div className="p-6 bg-gray-50">
                          <h3 className="text-lg font-medium text-gray-700 mb-4">Modifier les informations personnelles</h3>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Nom complet</label>
                              <input
                                type="text"
                                name="name"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={editValues.personalInfo.name}
                                onChange={(e) => handleInputChange(e, 'personalInfo')}
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                              <input
                                type="email"
                                name="email"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={editValues.personalInfo.email}
                                onChange={(e) => handleInputChange(e, 'personalInfo')}
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Titre du poste</label>
                              <input
                                type="text"
                                name="job_title"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={editValues.personalInfo.job_title}
                                onChange={(e) => handleInputChange(e, 'personalInfo')}
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                              <input
                                type="text"
                                name="phone"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={editValues.personalInfo.phone}
                                onChange={(e) => handleInputChange(e, 'personalInfo')}
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">Pays</label>
                              <input
                                type="text"
                                name="country"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={editValues.personalInfo.country}
                                onChange={(e) => handleInputChange(e, 'personalInfo')}
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn</label>
                              <input
                                type="text"
                                name="linkedin"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={editValues.personalInfo.linkedin}
                                onChange={(e) => handleInputChange(e, 'personalInfo')}
                              />
                            </div>
                            
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">GitHub</label>
                              <input
                                type="text"
                                name="github"
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={editValues.personalInfo.github}
                                onChange={(e) => handleInputChange(e, 'personalInfo')}
                              />
                            </div>
                          </div>
                          
                          <div className="flex justify-end space-x-3">
                            <button
                              type="button"
                              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
                              onClick={() => toggleEdit('personalInfo')}
                            >
                              Annuler
                            </button>
                            <button
                              type="button"
                              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                              onClick={savePersonalInfo}
                              disabled={isSaving}
                            >
                              {isSaving ? 'Enregistrement...' : 'Enregistrer'}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                {/* 2. Section Expérience Professionnelle */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-blue-50 p-4 border-b border-gray-200 flex justify-between items-center cursor-pointer"
                      onClick={() => toggleSection('experience')}>
                    <h2 className="text-lg font-semibold text-gray-800">Expérience Professionnelle</h2>
                    <button className="text-gray-500 hover:text-gray-700">
                      {expandedSections.experience ? (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  </div>
                  
                  {expandedSections.experience && (
                    <div className="p-4">
                      {experiences.length === 0 ? (
                        <p className="text-gray-500">Aucune expérience professionnelle trouvée</p>
                      ) : (
                        <div className="space-y-6">
                          {experiences.map((exp, index) => (
                            <div key={index} className="border-b border-gray-200 pb-6 last:border-b-0 last:pb-0">
                              <div className="flex justify-between">
                                <h3 className="font-bold text-lg">{exp.JobTitle}</h3>
                                <span className="text-sm text-gray-500">{exp.RelevanceScore} Relevance</span>
                              </div>
                              <p className="text-gray-700 font-medium">{exp.Company} {exp.Location && `- ${exp.Location}`}</p>
                              <p className="text-gray-500 mb-3">{exp.StartDate} - {exp.EndDate}</p>
                              
                              {exp.Responsibilities && exp.Responsibilities.length > 0 && (
                                <div className="mb-3">
                                  <h4 className="font-medium text-gray-700 mb-1">Responsabilités:</h4>
                                  <ul className="list-disc list-inside ml-2 space-y-1">
                                    {exp.Responsibilities.map((resp, i) => (
                                      <li key={i} className="text-gray-600">{resp}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              
                              {exp.Achievements && exp.Achievements.length > 0 && (
                                <div className="mb-3">
                                  <h4 className="font-medium text-gray-700 mb-1">Réalisations:</h4>
                                  <ul className="list-disc list-inside ml-2 space-y-1">
                                    {exp.Achievements.map((achievement, i) => (
                                      <li key={i} className="text-gray-600">{achievement}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              
                              {exp.ToolsAndTechnologies && exp.ToolsAndTechnologies.length > 0 && (
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-1">Technologies utilisées:</h4>
                                  <div className="flex flex-wrap gap-2">
                                    {exp.ToolsAndTechnologies.map((tech, i) => (
                                      <span key={i} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                        {tech}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                {/* 3. Section Formation & Certifications */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-blue-50 p-4 border-b border-gray-200 flex justify-between items-center cursor-pointer"
                      onClick={() => toggleSection('education')}>
                    <h2 className="text-lg font-semibold text-gray-800">Formation & Certifications</h2>
                    <button className="text-gray-500 hover:text-gray-700">
                      {expandedSections.education ? (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  </div>
                  
                  {expandedSections.education && (
                    <div className="p-4">
                      {degrees.length > 0 && (
                        <div className="mb-6">
                          <h3 className="font-medium text-gray-700 mb-3">Diplômes</h3>
                          <div className="space-y-4">
                            {degrees.map((degree, index) => (
                              <div key={index} className="border-l-4 border-blue-500 pl-4 py-1">
                                <h4 className="font-bold">{degree.DegreeName}</h4>
                                {degree.Specialization && (
                                  <p className="text-gray-700">Spécialisation: {degree.Specialization}</p>
                                )}
                                <p className="text-gray-600">{degree.CountryOrInstitute}</p>
                                <p className="text-gray-500 text-sm">{degree.Date}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {certifications.length > 0 && (
                        <div>
                          <h3 className="font-medium text-gray-700 mb-3">Certifications</h3>
                          <div className="space-y-4">
                            {certifications.map((cert, index) => (
                              <div key={index} className="border-l-4 border-green-500 pl-4 py-1">
                                <h4 className="font-bold">{cert.CertificationName}</h4>
                                <p className="text-gray-600">{cert.IssuingOrganization}</p>
                                <p className="text-gray-500 text-sm">{cert.IssueDate}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {degrees.length === 0 && certifications.length === 0 && (
                        <p className="text-gray-500">Aucune information sur la formation ou les certifications trouvée</p>
                      )}
                    </div>
                  )}
                </div>

                {/* 4. Section Compétences */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-blue-50 p-4 border-b border-gray-200 flex justify-between items-center cursor-pointer">
                    <h2 
                      className="text-lg font-semibold text-gray-800"
                      onClick={() => toggleSection('skills')}
                    >
                      Compétences
                    </h2>
                    <div className="flex items-center">
                      {!isEditing.hardSkills && !isEditing.softSkills && (
                        <button 
                          className="mr-3 text-blue-500 hover:text-blue-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleEdit('hardSkills');
                          }}
                          title="Modifier les compétences"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                          </svg>
                        </button>
                      )}
                      <button 
                        className="text-gray-500 hover:text-gray-700"
                        onClick={() => toggleSection('skills')}
                      >
                        {expandedSections.skills ? (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                  
                  {expandedSections.skills && (
                    <div className="p-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Compétences techniques */}
                        <div>
                          <div className="flex justify-between items-center mb-4">
                            <h3 className="font-medium text-gray-700">Compétences techniques</h3>
                            {!isEditing.hardSkills && !isEditing.softSkills && (
                              <button
                                className="text-blue-500 hover:text-blue-700 text-sm"
                                onClick={() => toggleEdit('hardSkills')}
                              >
                                Modifier
                              </button>
                            )}
                          </div>
                          
                          {!isEditing.hardSkills ? (
                            // Mode affichage des compétences techniques
                            hardSkills.length === 0 ? (
                              <p className="text-gray-500">Aucune compétence technique trouvée</p>
                            ) : (
                              <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="flex flex-wrap gap-2">
                                  {hardSkills.map((skill, index) => (
                                    <span key={index} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )
                          ) : (
                            // Mode édition des compétences techniques
                            <div className="bg-blue-50 p-4 rounded-lg">
                              <div className="flex flex-wrap gap-2 mb-3">
                                {editValues.hardSkills.map((skill, index) => (
                                  <div key={index} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center">
                                    {skill}
                                    <button
                                      type="button"
                                      className="ml-2 text-blue-500 hover:text-red-500"
                                      onClick={() => removeSkill('hard', index)}
                                    >
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                      </svg>
                                    </button>
                                  </div>
                                ))}
                              </div>
                              
                              <div className="flex items-center mb-3">
                                <input
                                  type="text"
                                  name="newSkill"
                                  className="flex-grow px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  value={editValues.newSkill}
                                  onChange={(e) => handleInputChange(e, 'skills')}
                                  placeholder="Nouvelle compétence..."
                                  onKeyPress={(e) => e.key === 'Enter' && addSkill('hard')}
                                />
                                <button
                                  type="button"
                                  className="px-4 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  onClick={() => addSkill('hard')}
                                >
                                  Ajouter
                                </button>
                              </div>
                              
                              <div className="flex justify-end space-x-3 mt-3">
                                <button
                                  type="button"
                                  className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50"
                                  onClick={() => toggleEdit('hardSkills')}
                                >
                                  Annuler
                                </button>
                                <button
                                  type="button"
                                  className="px-3 py-1 bg-blue-500 text-white text-sm rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  onClick={() => saveSkills('hard')}
                                  disabled={isSaving}
                                >
                                  {isSaving ? 'Enregistrement...' : 'Enregistrer'}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {/* Compétences personnelles */}
                        <div>
                          <div className="flex justify-between items-center mb-4">
                            <h3 className="font-medium text-gray-700">Compétences personnelles</h3>
                            {!isEditing.hardSkills && !isEditing.softSkills && (
                              <button
                                className="text-blue-500 hover:text-blue-700 text-sm"
                                onClick={() => toggleEdit('softSkills')}
                              >
                                Modifier
                              </button>
                            )}
                          </div>
                          
                          {!isEditing.softSkills ? (
                            // Mode affichage des compétences personnelles
                            softSkills.length === 0 ? (
                              <p className="text-gray-500">Aucune compétence personnelle trouvée</p>
                            ) : (
                              <div className="bg-gray-50 p-4 rounded-lg">
                                <div className="flex flex-wrap gap-2">
                                  {softSkills.map((skill, index) => (
                                    <span key={index} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )
                          ) : (
                            // Mode édition des compétences personnelles
                            <div className="bg-green-50 p-4 rounded-lg">
                              <div className="flex flex-wrap gap-2 mb-3">
                                {editValues.softSkills.map((skill, index) => (
                                  <div key={index} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center">
                                    {skill}
                                    <button
                                      type="button"
                                      className="ml-2 text-green-500 hover:text-red-500"
                                      onClick={() => removeSkill('soft', index)}
                                    >
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                      </svg>
                                    </button>
                                  </div>
                                ))}
                              </div>
                              
                              <div className="flex items-center mb-3">
                                <input
                                  type="text"
                                  name="newSkill"
                                  className="flex-grow px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-green-500"
                                  value={editValues.newSkill}
                                  onChange={(e) => handleInputChange(e, 'skills')}
                                  placeholder="Nouvelle compétence..."
                                  onKeyPress={(e) => e.key === 'Enter' && addSkill('soft')}
                                />
                                <button
                                  type="button"
                                  className="px-4 py-2 bg-green-500 text-white rounded-r-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500"
                                  onClick={() => addSkill('soft')}
                                >
                                  Ajouter
                                </button>
                              </div>
                              
                              <div className="flex justify-end space-x-3 mt-3">
                                <button
                                  type="button"
                                  className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50"
                                  onClick={() => toggleEdit('softSkills')}
                                >
                                  Annuler
                                </button>
                                <button
                                  type="button"
                                  className="px-3 py-1 bg-green-500 text-white text-sm rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500"
                                  onClick={() => saveSkills('soft')}
                                  disabled={isSaving}
                                >
                                  {isSaving ? 'Enregistrement...' : 'Enregistrer'}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* 5. Section Projets */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-blue-50 p-4 border-b border-gray-200 flex justify-between items-center cursor-pointer"
                      onClick={() => toggleSection('projects')}>
                    <h2 className="text-lg font-semibold text-gray-800">Projets</h2>
                    <button className="text-gray-500 hover:text-gray-700">
                      {expandedSections.projects ? (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  </div>
                  
                  {expandedSections.projects && (
                    <div className="p-4">
                      {projects.length === 0 ? (
                        <p className="text-gray-500">Aucun projet trouvé</p>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {projects.map((project, index) => (
                            <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                              <h3 className="font-bold text-lg">{project.ProjectName}</h3>
                              {project.Role && <p className="text-gray-700 font-medium">Rôle: {project.Role}</p>}
                              {project.Period && <p className="text-gray-500 mb-2">{project.Period}</p>}
                              
                              {project.Description && (
                                <div className="mb-3">
                                  <h4 className="font-medium text-gray-700 mb-1">Description:</h4>
                                  <p className="text-gray-600">{project.Description}</p>
                                </div>
                              )}
                              
                              {project.TechnologiesUsed && project.TechnologiesUsed.length > 0 && (
                                <div>
                                  <h4 className="font-medium text-gray-700 mb-1">Technologies utilisées:</h4>
                                  <div className="flex flex-wrap gap-2">
                                    {project.TechnologiesUsed.map((tech, i) => (
                                      <span key={i} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                        {tech}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              {project.URL && (
                                <div className="mt-3">
                                  <a 
                                    href={project.URL.startsWith('http') ? project.URL : `https://${project.URL}`} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-500 hover:underline text-sm flex items-center">
                                    Voir le projet
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
                                      <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                                      <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                                    </svg>
                                  </a>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Onglet Gestion de Contrat */}
            {activeTab === 'contract' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-blue-50 p-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-800">Gestion du Contrat</h2>
                </div>
                
                <form onSubmit={handleContractSubmit} className="p-6">
                  {saveMessage && (
                    <div className={`mb-6 p-3 rounded-md ${saveMessage.includes('succès') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {saveMessage}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <div className="mb-6">
                        <label className="block text-gray-700 font-medium mb-2">Statut du contrat</label>
                        <select 
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          value={contractStatus}
                          onChange={(e) => setContractStatus(e.target.value)}
                        >
                          <option value="pending">En attente</option>
                          <option value="negotiation">En négociation</option>
                          <option value="offered">Offre envoyée</option>
                          <option value="signed">Contrat signé</option>
                          <option value="rejected">Refusé</option>
                        </select>
                      </div>
                      
                      <div className="mb-6">
                        <label className="block text-gray-700 font-medium mb-2">Type de contrat</label>
                        <select 
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          value={contractType}
                          onChange={(e) => setContractType(e.target.value)}
                        >
                          <option value="CDI">CDI</option>
                          <option value="CDD">CDD</option>
                          <option value="Freelance">Freelance</option>
                          <option value="Alternance">Alternance</option>
                          <option value="Stage">Stage</option>
                        </select>
                      </div>
                      
                      <div className="mb-6">
                        <label className="block text-gray-700 font-medium mb-2">Salaire proposé</label>
                        <input 
                          type="text" 
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="ex: 45 000 € brut annuel"
                          value={contractSalary}
                          onChange={(e) => setContractSalary(e.target.value)}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <div className="mb-6">
                        <label className="block text-gray-700 font-medium mb-2">Date de début</label>
                        <input 
                          type="date" 
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          value={contractStartDate}
                          onChange={(e) => setContractStartDate(e.target.value)}
                        />
                      </div>
                      
                      <div className="mb-6">
                        <label className="block text-gray-700 font-medium mb-2">Date de fin {contractType === 'CDI' && '(facultatif)'}</label>
                        <input 
                          type="date" 
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          value={contractEndDate}
                          onChange={(e) => setContractEndDate(e.target.value)}
                        />
                      </div>
                      
                      <div className="mb-6">
                        <label className="block text-gray-700 font-medium mb-2">Notes</label>
                        <textarea 
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-28"
                          placeholder="Informations complémentaires sur le contrat..."
                          value={contractNotes}
                          onChange={(e) => setContractNotes(e.target.value)}
                        ></textarea>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-end mt-4">
                    <button 
                      type="button"
                      className="mr-3 px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Annuler
                    </button>
                    <button 
                      type="submit"
                      className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      Enregistrer
                    </button>
                  </div>
                </form>
              </div>
            )}
            
            {/* Onglet CV PDF */}
            {activeTab === 'resume' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="bg-blue-50 p-4 border-b border-gray-200 flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-800">Curriculum Vitae</h2>
                  <button 
                    onClick={handlePdfDownload}
                    className="text-blue-500 hover:text-blue-700 flex items-center text-sm"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    Télécharger
                  </button>
                </div>
                
                <div className="p-4">
                  <PDFViewer 
                    url={`/candidates/${id}/resume`} 
                    title={`CV de ${candidate.candidate.name}`} 
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <ToastContainer position="top-right" autoClose={3000} />
    </div>
  );
};
  
export default CandidateProfile;