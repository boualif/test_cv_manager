import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';

const CandidateList = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const { currentUser } = useAuth();
// À ajouter après cette ligne: const { currentUser } = useAuth();
  const [candidateToDelete, setCandidateToDelete] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const statusOptions = {
    pending: { label: 'En attente', color: 'bg-gray-100 text-gray-800' },
    review: { label: 'En cours d\'évaluation', color: 'bg-blue-100 text-blue-800' },
    interview: { label: 'Entretien programmé', color: 'bg-purple-100 text-purple-800' },
    offered: { label: 'Offre envoyée', color: 'bg-yellow-100 text-yellow-800' },
    hired: { label: 'Embauché', color: 'bg-green-100 text-green-800' },
    rejected: { label: 'Rejeté', color: 'bg-red-100 text-red-800' }
  };

  const columns = [
    { field: 'name', header: 'Nom', sortable: true },
    { field: 'email', header: 'Email', sortable: true },
    { field: 'job_title', header: 'Titre du poste', sortable: true },
    { field: 'added_by', header: 'Ajouté par', sortable: true },
    { field: 'created_at', header: 'Date d\'ajout', sortable: true },
    { field: 'status', header: 'Statut', sortable: true },
    { field: 'actions', header: 'Actions', sortable: false }
  ];
// Après la fonction handleChangeItemsPerPage
const setShowDeleteModal = (candidateId) => {
  setCandidateToDelete(candidateId);
};

const closeDeleteModal = () => {
  setCandidateToDelete(null);
};

const handleDeleteCandidate = async () => {
  if (!candidateToDelete) return;
  
  try {
    setIsSaving(true);
    await api.delete(`candidates/candidates/${candidateToDelete}`);
    setCandidates(candidates.filter(candidate => candidate.id !== candidateToDelete));
    closeDeleteModal();
  } catch (error) {
    console.error('Error deleting candidate:', error);
  } finally {
    setIsSaving(false);
  }
};
  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/candidates');
      
      
      // Only add random status if needed, but keep the added_by from the API
      const enrichedCandidates = response.data.map(candidate => ({
        ...candidate,
        status: getRandomStatus(),
        // No need to set added_by as it should come from the backend now
      }));
      
      setCandidates(enrichedCandidates);
      setError('');
    } catch (error) {
      console.error('Error fetching candidates:', error);
      setError('Impossible de charger la liste des candidats');
      if (error.response && error.response.status === 401) {
        setCandidates([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const getRandomStatus = () => {
    const statuses = Object.keys(statusOptions);
    return statuses[Math.floor(Math.random() * statuses.length)];
  };

  const getRandomRecruiter = () => {
    const recruiters = ['Thomas D.', 'Sarah L.', 'Marc B.', 'Julie K.'];
    return recruiters[Math.floor(Math.random() * recruiters.length)];
  };

  const handleSort = (field) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const handleChangeItemsPerPage = (e) => {
    setItemsPerPage(parseInt(e.target.value));
    setCurrentPage(1);
  };

  const filteredCandidates = candidates.filter(candidate => {
    const searchLower = searchTerm.toLowerCase();
    return (
      candidate.name.toLowerCase().includes(searchLower) ||
      candidate.email.toLowerCase().includes(searchLower) ||
      candidate.job_title.toLowerCase().includes(searchLower) ||
      candidate.added_by.toLowerCase().includes(searchLower)
    );
  });

  const sortedCandidates = [...filteredCandidates].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];

    if (sortField === 'created_at') {
      aValue = new Date(a.created_at).getTime();
      bValue = new Date(b.created_at).getTime();
    }

    if (aValue < bValue) {
      return sortDirection === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortDirection === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const totalPages = Math.ceil(filteredCandidates.length / itemsPerPage);
  const paginatedCandidates = sortedCandidates.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const renderStatus = (status) => {
    const statusInfo = statusOptions[status] || statusOptions.pending;
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${statusInfo.color}`}>
        {statusInfo.label}
      </span>
    );
  };

  const renderSortIcon = (field) => {
    if (field !== sortField) {
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
          <path d="M5 12a1 1 0 102 0V6.414l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L5 6.414V12zM15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z" />
        </svg>
      );
    } else if (sortDirection === 'asc') {
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
        </svg>
      );
    } else {
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      );
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
      <div className="flex-1 p-6 overflow-x-auto">
        <div className="bg-white shadow-md rounded-lg">
          <div className="p-4 border-b bg-gray-50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-800">Liste des Candidats</h2>
              <p className="text-gray-600 text-sm mt-1">
                {filteredCandidates.length} candidat(s) trouvé(s)
              </p>
            </div>
            <div className="w-full md:w-auto flex flex-col md:flex-row gap-3">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Rechercher..."
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-64"
                  value={searchTerm}
                  onChange={handleSearch}
                />
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 text-gray-400 absolute left-3 top-2.5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <Link
                to="/upload"
                className="bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
                Ajouter un candidat
              </Link>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  {columns.map((column) => (
                    <th 
                      key={column.field}
                      className="py-3 px-4 text-left text-xs font-medium text-gray-600 uppercase tracking-wider whitespace-nowrap"
                    >
                      {column.sortable ? (
                        <button 
                          className="flex items-center focus:outline-none" 
                          onClick={() => handleSort(column.field)}
                        >
                          {column.header}
                          {renderSortIcon(column.field)}
                        </button>
                      ) : (
                        column.header
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedCandidates.length === 0 ? (
                  <tr>
                    <td colSpan={columns.length} className="py-6 px-4 text-center text-gray-500">
                      {searchTerm 
                        ? "Aucun candidat trouvé correspondant à votre recherche" 
                        : "Aucun candidat trouvé. Ajoutez des candidats pour commencer."
                      }
                    </td>
                  </tr>
                ) : (
                  paginatedCandidates.map((candidate) => (
                    <tr key={candidate.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{candidate.name}</td>
                      <td className="py-3 px-4 text-gray-600">{candidate.email}</td>
                      <td className="py-3 px-4">{candidate.job_title}</td>
                      <td className="py-3 px-4">{candidate.added_by}</td>
                      <td className="py-3 px-4 text-gray-600 whitespace-nowrap">
                        {new Date(candidate.created_at).toLocaleDateString()} 
                        <span className="text-xs text-gray-500 ml-1">
                          {new Date(candidate.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {renderStatus(candidate.status)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <Link to={`/candidates/${candidate.id}`} 

                            className="text-blue-500 hover:text-blue-700"
                            title="Voir le profil"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                            </svg>
                          </Link>
                          <button 
                            className="text-gray-600 hover:text-gray-800"
                            title="Modifier le statut"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                              <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
                              <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" />
                            </svg>
                          </button>
                          {currentUser && currentUser.role === 'admin' && (
                            <button 
                              onClick={() => setShowDeleteModal(candidate.id)}
                              className="text-red-500 hover:text-red-700"
                              title="Supprimer le candidat"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="p-4 border-t flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0 flex items-center">
              <span className="text-sm text-gray-600 mr-2">Afficher</span>
              <select
                className="border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={itemsPerPage}
                onChange={handleChangeItemsPerPage}
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
              <span className="text-sm text-gray-600 ml-2">éléments par page</span>
            </div>

            <div className="flex items-center">
              <button
                className="px-3 py-1 border border-gray-300 rounded-l-md bg-white text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                Précédent
              </button>
              <div className="px-4 py-1 border-t border-b border-gray-300 bg-white text-gray-700">
                Page {currentPage} sur {totalPages || 1}
              </div>
              <button
                className="px-3 py-1 border border-gray-300 rounded-r-md bg-white text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={currentPage === totalPages || totalPages === 0}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                Suivant
              </button>
            </div>
          </div>
          {candidateToDelete && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg p-6 max-w-md w-full">
      <h3 className="text-xl font-bold mb-4">Confirmer la suppression</h3>
      <p className="mb-6">Êtes-vous sûr de vouloir supprimer ce candidat ? Cette action est irréversible.</p>
      <div className="flex justify-end space-x-3">
        <button
          onClick={closeDeleteModal}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
          disabled={isSaving}
        >
          Annuler
        </button>
        <button
          onClick={handleDeleteCandidate}
          className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none"
          disabled={isSaving}
        >
          {isSaving ? 'Suppression...' : 'Supprimer'}
        </button>
      </div>
    </div>
  </div>
)}
        </div>
      </div>
    </div>
  );
};

export default CandidateList;