import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const UploadCV = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [uploadResults, setUploadResults] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  // Handle file selection
  const handleFileSelect = (selectedFiles) => {
    const fileArray = Array.from(selectedFiles);
    
    // Filter for supported file types
    const supportedFiles = fileArray.filter(file => {
      const fileType = file.type;
      const fileName = file.name.toLowerCase();
      return (
        fileType === 'application/pdf' ||
        fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        fileType === 'application/msword' ||
        fileName.endsWith('.pdf') ||
        fileName.endsWith('.docx') ||
        fileName.endsWith('.doc')
      );
    });

    // Show warning for unsupported files
    const unsupportedFiles = fileArray.filter(file => !supportedFiles.includes(file));
    if (unsupportedFiles.length > 0) {
      toast.warning(`${unsupportedFiles.length} fichier(s) non supporté(s) ignoré(s). Seuls les fichiers PDF et DOCX sont acceptés.`);
    }

    if (supportedFiles.length === 0) {
      toast.error('Aucun fichier supporté sélectionné. Veuillez choisir des fichiers PDF ou DOCX.');
      return;
    }

    // Check file size limit (10MB per file)
    const oversizedFiles = supportedFiles.filter(file => file.size > 10 * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      toast.error(`${oversizedFiles.length} fichier(s) trop volumineux (limite: 10MB par fichier).`);
      return;
    }

    // Check total number of files (max 20)
    const currentFileCount = files.length;
    const newFileCount = supportedFiles.length;
    if (currentFileCount + newFileCount > 20) {
      toast.error(`Limite de 20 fichiers dépassée. Vous avez ${currentFileCount} fichiers et tentez d'en ajouter ${newFileCount}.`);
      return;
    }

    // Add files to the list
    setFiles(prevFiles => [...prevFiles, ...supportedFiles]);
    toast.success(`${supportedFiles.length} fichier(s) ajouté(s) avec succès.`);
  };

  // Handle drag and drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  // Handle file input change
  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files);
    }
    // Reset input value to allow selecting the same file again
    e.target.value = '';
  };

  // Remove file from list
  const removeFile = (index) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
    toast.info('Fichier supprimé de la liste.');
  };

  // Clear all files
  const clearAllFiles = () => {
    setFiles([]);
    setUploadResults(null);
    toast.info('Tous les fichiers ont été supprimés.');
  };

  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data URL prefix (data:application/pdf;base64,)
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Get file type icon
  const getFileIcon = (file) => {
    const fileName = file.name.toLowerCase();
    if (fileName.endsWith('.pdf')) {
      return (
        <svg className="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    } else {
      return (
        <svg className="w-8 h-8 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
  };

  // Handle upload
  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Veuillez sélectionner au moins un fichier à télécharger.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadResults(null);

    try {
      // Convert all files to base64
      toast.info('Préparation des fichiers...');
      const base64Files = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        try {
          const base64 = await fileToBase64(file);
          base64Files.push(base64);
          setUploadProgress(((i + 1) / files.length) * 50); // 50% for file conversion
        } catch (error) {
          toast.error(`Erreur lors de la conversion du fichier: ${file.name}`);
          throw error;
        }
      }

      toast.info('Envoi des fichiers au serveur...');
      setUploadProgress(60);

      // Send to server
      const response = await api.post('/candidates/cv/add', {
        fileContents: base64Files
      });

      setUploadProgress(100);
      setUploadResults(response.data);

      // Show results
      const { success, duplicates, error_count, file_types_processed } = response.data;
      
      if (success.length > 0) {
        toast.success(`${success.length} CV(s) téléchargé(s) avec succès!`);
      }
      
      if (duplicates.length > 0) {
        toast.warning(`${duplicates.length} candidat(s) déjà existant(s) ignoré(s).`);
      }
      
      if (error_count > 0) {
        toast.error(`${error_count} erreur(s) lors du traitement.`);
      }

      // Log file types processed
      if (file_types_processed) {
        console.log('Types de fichiers traités:', file_types_processed);
      }

    } catch (error) {
      console.error('Upload error:', error);
      setUploadProgress(0);
      
      if (error.response && error.response.status === 401) {
        toast.error('Session expirée. Redirection vers la connexion...');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        toast.error(`Erreur lors du téléchargement: ${error.message || 'Erreur inconnue'}`);
      }
    } finally {
      setUploading(false);
    }
  };

  // Handle navigation to results
  const navigateToCandidate = (candidateId) => {
    navigate(`/candidates/${candidateId}`);
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Sidebar />
      <div className="md:ml-64 flex-grow p-6">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-800">Télécharger des CV</h1>
                <p className="text-gray-600 mt-1">
                  Ajoutez des CV en format PDF ou DOCX pour analyser automatiquement les profils candidats
                </p>
              </div>
              <button
                onClick={() => navigate('/candidates')}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                </svg>
                Retour
              </button>
            </div>
          </div>

          {/* Upload Area */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="space-y-6">
              {/* Drag & Drop Zone */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <div className="flex flex-col items-center">
                  <svg className="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <h3 className="text-lg font-medium text-gray-700 mb-2">
                    Glissez-déposez vos fichiers ici
                  </h3>
                  <p className="text-gray-500 mb-4">
                    ou cliquez pour sélectionner des fichiers
                  </p>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium"
                    disabled={uploading}
                  >
                    Sélectionner des fichiers
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword"
                    onChange={handleInputChange}
                    className="hidden"
                  />
                </div>
              </div>

              {/* File Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <div className="text-sm">
                    <h4 className="text-blue-800 font-medium mb-1">Formats acceptés</h4>
                    <ul className="text-blue-700 space-y-1">
                      <li>• Fichiers PDF (.pdf)</li>
                      <li>• Documents Word (.docx, .doc)</li>
                      <li>• Taille maximale: 10 MB par fichier</li>
                      <li>• Maximum: 20 fichiers par envoi</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-800">
                  Fichiers sélectionnés ({files.length})
                </h3>
                <button
                  onClick={clearAllFiles}
                  className="text-red-500 hover:text-red-700 text-sm font-medium"
                  disabled={uploading}
                >
                  Tout supprimer
                </button>
              </div>
              
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      {getFileIcon(file)}
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-800">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(file.size)} • {file.type || 'Type inconnu'}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700 p-1"
                      disabled={uploading}
                      title="Supprimer ce fichier"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Progress */}
          {uploading && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Progression du téléchargement</span>
                <span className="text-sm text-gray-500">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Upload Results */}
          {uploadResults && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-medium text-gray-800 mb-4">Résultats du téléchargement</h3>
              
              {/* Success Results */}
              {uploadResults.success && uploadResults.success.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-green-600 font-medium mb-2">
                    ✅ CV traités avec succès ({uploadResults.success.length})
                  </h4>
                  <div className="space-y-2">
                    {uploadResults.success.map((result, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                        <span className="text-sm text-green-800">
                          Fichier {result.file_name + 1} - Candidat ID: {result.candidate_id}
                        </span>
                        <button
                          onClick={() => navigateToCandidate(result.candidate_id)}
                          className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                        >
                          Voir le profil
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Duplicate Results */}
              {uploadResults.duplicates && uploadResults.duplicates.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-yellow-600 font-medium mb-2">
                    ⚠️ Candidats déjà existants ({uploadResults.duplicates.length})
                  </h4>
                  <div className="space-y-2">
                    {uploadResults.duplicates.map((duplicate, index) => (
                      <div key={index} className="p-3 bg-yellow-50 rounded-lg">
                        <span className="text-sm text-yellow-800">
                          Fichier {duplicate.file_index + 1}: {duplicate.name} ({duplicate.email})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error Results */}
              {uploadResults.error_count > 0 && (
                <div className="mb-4">
                  <h4 className="text-red-600 font-medium mb-2">
                    ❌ Erreurs de traitement ({uploadResults.error_count})
                  </h4>
                  <div className="p-3 bg-red-50 rounded-lg">
                    <span className="text-sm text-red-800">
                      {uploadResults.error_count} fichier(s) n'ont pas pu être traités. 
                      Vérifiez les formats et la qualité des fichiers.
                    </span>
                  </div>
                </div>
              )}

              {/* File Types Summary */}
              {uploadResults.file_types_processed && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <h4 className="text-gray-700 font-medium mb-2">Types de fichiers traités</h4>
                  <div className="text-sm text-gray-600">
                    PDF: {uploadResults.file_types_processed.pdf || 0} • 
                    DOCX: {uploadResults.file_types_processed.docx || 0} • 
                    Erreurs: {uploadResults.file_types_processed.errors || 0}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload Button */}
          <div className="flex justify-center">
            <button
              onClick={handleUpload}
              disabled={files.length === 0 || uploading}
              className={`px-8 py-3 rounded-lg font-medium text-white ${
                files.length === 0 || uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600'
              }`}
            >
              {uploading ? (
                <div className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                  </svg>
                  Téléchargement en cours...
                </div>
              ) : (
                `Télécharger ${files.length} fichier(s)`
              )}
            </button>
          </div>
        </div>
      </div>
      <ToastContainer 
        position="top-right" 
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
    </div>
  );
};

export default UploadCV;
