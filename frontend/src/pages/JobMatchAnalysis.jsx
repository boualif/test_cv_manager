import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import jobService from '../services/jobService';
import candidateService from '../services/candidateService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import PDFViewer from '../components/PDFViewer';

const JobMatchAnalysis = () => {
  const [showPdf, setShowPdf] = useState(false);
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [analysisResults, setAnalysisResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [minScore, setMinScore] = useState(0.5);
  const [maxResults, setMaxResults] = useState(10);
  const [suggestions, setSuggestions] = useState([]);
  
  useEffect(() => {
    Promise.all([
      fetchJobDetails(),
      fetchCandidates(),
      fetchSuggestions()
    ]).then(() => {
      setLoading(false);
    }).catch(error => {
      setError('Une erreur est survenue lors du chargement des données');
      setLoading(false);
    });
  }, [id]);
  
  const fetchJobDetails = async () => {
    try {
      const data = await jobService.getJob(id);
      setJob(data);
    } catch (error) {
      console.error('Erreur lors du chargement des détails de l\'offre d\'emploi:', error);
      setError('Impossible de charger les détails de l\'offre d\'emploi');
      throw error;
    }
  };

  const parsePercentage = (percentageStr) => {
    if (!percentageStr) return 0;
    return parseFloat(String(percentageStr).replace('%', ''));
  };

  const calculateWeightedScore = (score, weight) => {
    const parsedScore = parsePercentage(score);
    return Math.round(parsedScore * weight);
  };

  const fetchCandidates = async () => {
    try {
      const data = await candidateService.getCandidates();
      setCandidates(data);
    } catch (error) {
      console.error('Erreur lors du chargement des candidats:', error);
      setError('Impossible de charger la liste des candidats');
      throw error;
    }
  };

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      const data = await jobService.suggestCandidatesForJob(id, maxResults, minScore);
      setSuggestions(data.suggested_candidates || []);
    } catch (error) {
      console.error('Erreur lors du chargement des suggestions:', error);
      if (error.code === 'CONNECTION_ERROR') {
        toast.error("Le serveur ne répond pas. Vérifiez que le backend est en cours d'exécution.");
      } else if (error.status === 500) {
        toast.error("Une erreur s'est produite sur le serveur. Vérifiez les logs du backend.");
      } else {
        toast.error(error.message || "Impossible de charger les suggestions de candidats");
      }
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };
  
  const toggleCandidateSelection = (candidateId) => {
    if (selectedCandidates.includes(candidateId)) {
      setSelectedCandidates(selectedCandidates.filter(id => id !== candidateId));
    } else {
      setSelectedCandidates([...selectedCandidates, candidateId]);
    }
  };
  
  const selectAllCandidates = () => {
    setSelectedCandidates(suggestions.map(candidate => candidate.id));
  };
  
  const clearSelection = () => {
    setSelectedCandidates([]);
  };
  
  const handleApplyFilters = async () => {
    setLoading(true);
    try {
      await fetchSuggestions();
    } catch (error) {
      toast.error("Erreur lors de l'application des filtres");
    } finally {
      setLoading(false);
    }
  };
  
  const handleAnalysis = async () => {
    if (selectedCandidates.length === 0) {
      toast.warning('Veuillez sélectionner au moins un candidat');
      return;
    }
    
    if (selectedCandidates.length > 10) {
      toast.info(`Vous avez sélectionné ${selectedCandidates.length} candidats. L'analyse peut prendre plusieurs minutes.`);
    }
    
    setAnalyzing(true);
    try {
      console.log('IDs des candidats sélectionnés:', selectedCandidates);
      console.log('Analyse avec tous les candidats:', selectedCandidates);
      
      const toastId = toast.loading(`Analyse en cours pour ${selectedCandidates.length} candidat(s). Cela peut prendre quelques minutes...`);
      
      const results = await jobService.analyzeJobMatch(id, selectedCandidates);
      
      toast.update(toastId, { 
        render: `Analyse terminée pour ${results.length} candidat(s)`, 
        type: "success", 
        isLoading: false,
        autoClose: 5000
      });
      
      console.log('Résultats reçus du service:', results);
      
      setAnalysisResults(results);
      if (results.length > 0) {
        setSelectedResult(0);
      }
    } catch (error) {
      console.error('Erreur lors de l\'analyse de correspondance:', error);
      toast.error(error.message || 'Une erreur est survenue lors de l\'analyse');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAutoAnalysis = async () => {
    setAnalyzing(true);
    try {
      const toastId = toast.loading("Recherche et analyse automatique des meilleurs candidats...");
      
      const results = await jobService.analyzeJobMatchAuto(id);
      
      toast.update(toastId, {
        render: `Analyse automatique terminée pour ${results.length} candidat(s)`,
        type: "success",
        isLoading: false,
        autoClose: 3000
      });
      
      setAnalysisResults(results);
      if (results.length > 0) {
        setSelectedResult(0);
      }
    } catch (error) {
      toast.error(error.message || "Une erreur est survenue lors de l'analyse automatique");
    } finally {
      setAnalyzing(false);
    }
  };
  
  const getMatchQualityClass = (quality) => {
    switch (quality) {
      case 'Excellent':
        return 'bg-green-300 text-green-900 font-bold px-2 py-0.5 rounded-full';
      case 'Très bon':
        return 'bg-blue-300 text-blue-900 font-bold px-2 py-0.5 rounded-full';
      case 'Bon':
        return 'bg-teal-300 text-teal-900 font-bold px-2 py-0.5 rounded-full';
      case 'Moyen':
        return 'bg-yellow-300 text-yellow-900 font-bold px-2 py-0.5 rounded-full';
      case 'Faible':
        return 'bg-red-300 text-red-900 font-bold px-2 py-0.5 rounded-full';
      default:
        return 'bg-gray-300 text-gray-900 font-bold px-2 py-0.5 rounded-full';
    }
  };
  
  const getScoreColor = (score) => {
    const numericScore = parseInt(String(score).replace('%', ''));
    if (numericScore >= 80) return 'bg-green-300 text-green-900 font-bold';
    if (numericScore >= 70) return 'bg-blue-300 text-blue-900 font-bold';
    if (numericScore >= 60) return 'bg-teal-300 text-teal-900 font-bold';
    if (numericScore >= 50) return 'bg-yellow-300 text-yellow-900 font-bold';
    return 'bg-red-300 text-red-900 font-bold';
  };
  
  const getJobTypeLabel = (type) => {
    switch (type) {
      case 'technique':
        return <span className="px-2 py-1 rounded-full text-xs"><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">Technique</span></span>;
      case 'fonctionnel':
        return <span className="px-2 py-1 rounded-full text-xs"><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">Fonctionnel</span></span>;
      case 'technico-fonctionnel':
        return <span className="px-2 py-1 rounded-full text-xs"><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">Technico-fonctionnel</span></span>;
      default:
        return <span className="px-2 py-1 rounded-full text-xs"><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">{type}</span></span>;
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
  
  return (
    <div className="flex min-h-screen">
      <div className="w-64 flex-shrink-0">
        <Sidebar />
      </div>
      <div className="flex-1 p-6">
        <div className="mb-6">
          <Link to={`/jobs/${id}`} className="text-blue-500 hover:underline flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Retour aux détails de l'offre
          </Link>
        </div>
        
        <div className="bg-white shadow-md rounded-lg overflow-hidden mb-6">
          <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
            <h1 className="text-xl font-bold text-gray-800">Analyse de correspondance avec l'offre d'emploi</h1>
            <div className="mt-2">
              <span className="text-gray-700 font-medium">{job.title}</span>
              <span className="mx-2">•</span>
              {getJobTypeLabel(job.job_type_etiquette)}
              {job.competence_phare && (
                <>
                  <span className="mx-2">•</span>
                  <span><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">{job.competence_phare}</span></span>
                </>
              )}
            </div>
          </div>
          
          {!analysisResults || analysisResults.length === 0 ? (
            <div className="p-4">
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-3">Candidats suggérés pour cette offre</h2>
                
                <div className="mb-6 bg-gray-50 p-4 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nombre max. de résultats</label>
                      <select
                        value={maxResults}
                        onChange={(e) => setMaxResults(parseInt(e.target.value))}
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                      >
                        <option value="5">5</option>
                        <option value="10">10</option>
                        <option value="20">20</option>
                        <option value="50">50</option>
                      </select>
                    </div>
                  </div>
                  <button
                    onClick={handleApplyFilters}
                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                  >
                    Appliquer les filtres
                  </button>
                </div>

                {suggestions.length === 0 ? (
                  <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
                    <p>Aucun candidat correspondant n'a été trouvé pour ce poste.</p>
                  </div>
                ) : (
                  <>
                    <div className="mb-4 flex justify-between items-center">
                      <p className="text-sm text-gray-600">{suggestions.length} candidat(s) trouvé(s)</p>
                      <div className="flex space-x-4">
                        <button
                          onClick={handleAnalysis}
                          disabled={selectedCandidates.length === 0 || analyzing}
                          className={`px-4 py-2 rounded text-white font-medium ${
                            selectedCandidates.length === 0 || analyzing
                              ? 'bg-gray-400 cursor-not-allowed'
                              : 'bg-blue-600 hover:bg-blue-700'
                          }`}
                        >
                          {analyzing ? 'Analyse en cours...' : 'Analyser les candidats sélectionnés'}
                        </button>
                      </div>
                    </div>
                    
                    <div className="border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 p-3 border-b border-gray-200 flex items-center">
                        <div className="w-8"></div>
                        <div className="flex-1 font-medium text-gray-600 text-sm">Nom</div>
                        <div className="w-1/4 hidden md:block font-medium text-gray-600 text-sm">Email</div>
                        <div className="w-1/5 hidden md:block font-medium text-gray-600 text-sm">Poste actuel</div>
                      </div>
                      
                      <div className="divide-y divide-gray-200 max-h-80 overflow-y-auto">
                        {suggestions.map(candidate => (
                          <div 
                            key={candidate.id} 
                            className={`p-3 flex items-center hover:bg-gray-50 transition-colors duration-150 ease-in-out ${
                              selectedCandidates.includes(candidate.id) ? 'bg-blue-50' : ''
                            }`}
                            onClick={() => toggleCandidateSelection(candidate.id)}
                          >
                            <div className="w-8 flex justify-center">
                              <input
                                type="checkbox"
                                checked={selectedCandidates.includes(candidate.id)}
                                onChange={() => {}}
                                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                              />
                            </div>
                            <div className="flex-1 truncate">
                              <div className="text-gray-800 font-medium">{candidate.name}</div>
                              {candidate.match_reason && (
                                <div className="text-xs text-gray-500 mt-1">{candidate.match_reason}</div>
                              )}
                              <div className="text-gray-500 text-xs md:hidden">{candidate.email}</div>
                            </div>
                            <div className="w-1/4 hidden md:block text-gray-600 text-sm truncate">{candidate.email}</div>
                            <div className="w-1/5 hidden md:block text-gray-600 text-sm truncate">{candidate.job_title || 'Non spécifié'}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="p-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-800">Résultats de l'analyse</h2>
                <button
                  onClick={() => setAnalysisResults([])}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-600 hover:bg-gray-50"
                >
                  Retour à la sélection
                </button>
              </div>
              
              {analysisResults.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {analysisResults.map((result, index) => (
                    <div
                      key={`result-${index}-${result.candidate_id || index}`}
                      className={`border rounded-lg overflow-hidden hover:shadow-md transition-shadow duration-150 ease-in-out cursor-pointer ${
                        selectedResult === index ? 'ring-2 ring-blue-500' : ''
                      }`}
                      onClick={() => setSelectedResult(index)}
                    >
                      <div className="p-4 border-b">
                        <div className="font-medium text-gray-800">{result.name || 'Candidat'}</div>
                        <div className="text-sm text-gray-500">{result.email || 'Email non disponible'}</div>
                      </div>
                      <div className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium text-gray-600">Score global:</div>
                          <div className={`text-xl font-bold ${getScoreColor(result.combined_score || result.final_score || '0%')}`}>
                            {result.combined_score || result.final_score || '0%'}
                            {result.combined_score && result.final_score && result.combined_score !== result.final_score && (
                              <div className="text-xs font-normal text-gray-500">
                                (Score final précédent: {result.final_score})
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center justify-between mb-2">
                          <div className={`text-sm px-2 py-0.5 rounded-full ${getMatchQualityClass(result.match_quality || 'Non évalué')}`}>
                            {result.match_quality || 'Non évalué'}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-yellow-800">
                  Aucun résultat d'analyse n'a été retourné. Veuillez réessayer ou sélectionner d'autres candidats.
                </div>
              )}
              
              {selectedResult !== null && analysisResults.length > 0 && selectedResult < analysisResults.length && (
                <div className="bg-gray-50 border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-800 mb-4">
                    Détails de l'analyse pour {analysisResults[selectedResult].name || 'ce candidat'}
                  </h3>

                  <div className={`grid ${showPdf ? 'lg:grid-cols-2' : 'grid-cols-1'} gap-4`}>
                    <div className={showPdf ? 'lg:w-1/10' : 'w-full'}>
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">Compétences correspondantes</h4>
                        {analysisResults[selectedResult].cv_analysis?.skills_match && analysisResults[selectedResult].cv_analysis.skills_match.length > 0 ? (
                          <div className="bg-white border border-green-200 rounded-md p-3">
                            <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                              {analysisResults[selectedResult].cv_analysis.skills_match.map((skill, idx) => (
                                <li key={idx}><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">{skill}</span></li>
                              ))}
                            </ul>
                          </div>
                        ) : (
                          <div className="bg-white border border-gray-200 rounded-md p-3 text-sm text-gray-500">
                            Aucune compétence correspondante n'a été identifiée.
                          </div>
                        )}
                      </div>

                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">Compétences manquantes</h4>
                        {analysisResults[selectedResult].cv_analysis?.skills_gaps && analysisResults[selectedResult].cv_analysis.skills_gaps.length > 0 ? (
                          <div className="bg-white border border-red-200 rounded-md p-3">
                            <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                              {analysisResults[selectedResult].cv_analysis.skills_gaps.map((skill, idx) => (
                                <li key={idx}><span className="bg-red-300 text-red-900 font-bold px-1 py-0.5 rounded-full">{skill}</span></li>
                              ))}
                            </ul>
                          </div>
                        ) : (
                          <div className="bg-white border border-gray-200 rounded-md p-3 text-sm text-gray-500">
                            Aucune compétence manquante n'a été identifiée.
                          </div>
                        )}
                      </div>

                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">Expérience correspondante</h4>
                        {analysisResults[selectedResult].cv_analysis?.job_title_and_experience_match ? (
                          <div className="bg-white border border-green-200 rounded-md p-3">
                            <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                              {Array.isArray(analysisResults[selectedResult].cv_analysis.job_title_and_experience_match) ? 
                                analysisResults[selectedResult].cv_analysis.job_title_and_experience_match.map((exp, idx) => (
                                  <li key={idx}>{exp}</li>
                                )) : 
                                <li>{analysisResults[selectedResult].cv_analysis.job_title_and_experience_match}</li>
                              }
                            </ul>
                          </div>
                        ) : (
                          <div className="bg-white border border-gray-200 rounded-md p-3 text-sm text-gray-500">
                            Aucune expérience correspondante n'a été identifiée.
                          </div>
                        )}
                      </div>

                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">Lacunes d'expérience</h4>
                        {analysisResults[selectedResult].cv_analysis?.job_title_and_experience_gaps ? (
                          <div className="bg-white border border-red-200 rounded-md p-3">
                            <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
                              {Array.isArray(analysisResults[selectedResult].cv_analysis.job_title_and_experience_gaps) ? 
                                analysisResults[selectedResult].cv_analysis.job_title_and_experience_gaps.map((exp, idx) => (
                                  <li key={idx}>{exp}</li>
                                )) : 
                                <li>{analysisResults[selectedResult].cv_analysis.job_title_and_experience_gaps}</li>
                              }
                            </ul>
                          </div>
                        ) : (
                          <div className="bg-white border border-gray-200 rounded-md p-3 text-sm text-gray-500">
                            Aucune lacune d'expérience n'a été identifiée.
                          </div>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Informations additionnelles</h4>
                          <div className="bg-white border border-gray-200 rounded-md p-3">
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600">Années d'expérience:</span>
                                <span className="font-medium text-gray-800">
                                  {analysisResults[selectedResult].cv_analysis?.years_of_experience || 'Non spécifié'}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Localisation:</span>
                                <span className="font-medium text-gray-800">
                                  {analysisResults[selectedResult].cv_analysis?.location || 'Non spécifié'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Forces et faiblesses</h4>
                          <div className="bg-white border border-gray-200 rounded-md p-3">
                            <div className="space-y-3 text-sm">
                              {analysisResults[selectedResult].cv_analysis?.general_strengths && 
                                analysisResults[selectedResult].cv_analysis.general_strengths.length > 0 && (
                                <div>
                                  <h5 className="text-gray-700 font-medium mb-1">Forces:</h5>
                                  <ul className="list-disc pl-5 space-y-1 text-gray-700">
                                    {Array.isArray(analysisResults[selectedResult].cv_analysis.general_strengths) ? 
                                      analysisResults[selectedResult].cv_analysis.general_strengths.map((strength, idx) => (
                                        <li key={idx}><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">{strength}</span></li>
                                      )) : 
                                      <li><span className="bg-green-300 text-green-900 font-bold px-1 py-0.5 rounded-full">{analysisResults[selectedResult].cv_analysis.general_strengths}</span></li>
                                    }
                                  </ul>
                                </div>
                              )}

                              {analysisResults[selectedResult].cv_analysis?.general_weaknesses && 
                                analysisResults[selectedResult].cv_analysis.general_weaknesses.length > 0 && (
                                <div>
                                  <h5 className="text-gray-700 font-medium mb-1">Faiblesses:</h5>
                                  <ul className="list-disc pl-5 space-y-1 text-gray-700">
                                    {Array.isArray(analysisResults[selectedResult].cv_analysis.general_weaknesses) ? 
                                      analysisResults[selectedResult].cv_analysis.general_weaknesses.map((weakness, idx) => (
                                        <li key={idx}><span className="bg-red-300 text-red-900 font-bold px-1 py-0.5 rounded-full">{weakness}</span></li>
                                      )) : 
                                      <li><span className="bg-red-300 text-red-900 font-bold px-1 py-0.5 rounded-full">{analysisResults[selectedResult].cv_analysis.general_weaknesses}</span></li>
                                    }
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">Coordonnées</h4>
                        <div className="bg-white border border-gray-200 rounded-md p-3">
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Email:</span>
                              <span className="font-medium text-gray-800">
                                {analysisResults[selectedResult].cv_analysis?.email || 'Non spécifié'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Téléphone:</span>
                              <span className="font-medium text-gray-800">
                                {analysisResults[selectedResult].cv_analysis?.phone || 'Non spécifié'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="mb-4">
                        <h4 className="font-medium text-gray-700 mb-2">Statut de l'analyse</h4>
                        <div className="bg-white border border-gray-200 rounded-md p-3 text-sm text-gray-700">
                          {analysisResults[selectedResult].status === 'success' ? (
                            <div className="flex items-center text-green-600">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                              Analyse réussie
                            </div>
                          ) : (
                            <div className="flex items-center text-red-600">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                              </svg>
                              {analysisResults[selectedResult].error || 'Échec de l\'analyse'}
                            </div>
                          )}
                        </div>
                      </div>

                      {analysisResults[selectedResult].candidate_id && (
                        <div className="mt-4 flex justify-end">
                          <button
                            onClick={() => setShowPdf(!showPdf)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors duration-150 ease-in-out flex items-center"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            {showPdf ? "Masquer le CV" : "Voir le CV du candidat"}
                          </button>
                        </div>
                      )}
                    </div>

                    {showPdf && analysisResults[selectedResult].candidate_id && (
                      <div className="bg-white border rounded-lg overflow-hidden">
                        <div className="bg-blue-50 p-4 border-b border-gray-200 flex justify-between items-center">
                          <h2 className="text-lg font-semibold text-gray-800">Curriculum Vitae</h2>
                          <a
                            href={`/candidates/${analysisResults[selectedResult].candidate_id}/resume`}
                            download={`cv_${analysisResults[selectedResult].name || 'candidat'}.pdf`}
                            className="text-blue-500 hover:text-blue-700 flex items-center text-sm"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                            Télécharger
                          </a>
                        </div>
                        <div className="p-4">
                          <PDFViewer
                            url={`/candidates/${analysisResults[selectedResult].candidate_id}/resume`}
                            title={`CV de ${analysisResults[selectedResult].name || 'candidat'}`}
                            style={{ height: '100%', width: '100%' }}
                            scale={1.0}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        <ToastContainer position="bottom-right" />
      </div>
    </div>
  );
};

export default JobMatchAnalysis;