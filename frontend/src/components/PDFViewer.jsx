import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api'; // Importer l'instance api configurée
import { useNavigate } from 'react-router-dom';

const PDFViewer = ({ url, title = "PDF Viewer" }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pdfBlob, setPdfBlob] = useState(null);
  const iframeRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (url) {
      const fetchPDF = async () => {
        try {
          setLoading(true);
          
          // Utiliser l'instance API configurée pour récupérer le PDF
          // Cela enverra automatiquement le token d'authentification
          const response = await api.get(url, {
            responseType: 'blob' // Important pour les fichiers binaires
          });
          
          // Créer un URL d'objet pour le blob
          const pdfBlobUrl = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
          setPdfBlob(pdfBlobUrl);
          setLoading(false);
        } catch (err) {
          console.error('Error fetching PDF:', err);
          
          // Gérer spécifiquement les erreurs 401 (non autorisé)
          if (err.response && err.response.status === 401) {
            setError('Your session has expired. Redirecting to login...');
            setTimeout(() => {
              navigate('/login', { state: { from: window.location.pathname } });
            }, 2000);
          } else {
            setError(`Unable to load PDF: ${err.message}`);
          }
          setLoading(false);
        }
      };
      
      fetchPDF();
      
      // Nettoyage de l'URL du blob lorsque le composant est démonté
      return () => {
        if (pdfBlob) {
          window.URL.revokeObjectURL(pdfBlob);
        }
      };
    } else {
      setError('No PDF URL provided');
      setLoading(false);
    }
  }, [url, navigate]);
  
  // Fonction pour télécharger le PDF
  const handleDownload = () => {
    if (pdfBlob) {
      const link = document.createElement('a');
      link.href = pdfBlob;
      link.download = `${title.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center w-full h-[600px] bg-gray-100 border border-gray-300 rounded">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading PDF...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center w-full h-[600px] bg-gray-100 border border-gray-300 rounded">
        <div className="text-center p-6">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-red-600 font-medium mb-2">Error Loading PDF</p>
          <p className="text-gray-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white border border-gray-300 rounded shadow-sm">
      <div className="bg-gray-100 p-3 border-b border-gray-300 flex justify-between items-center">
        <h3 className="font-medium text-gray-700">{title}</h3>
        <button 
          onClick={handleDownload}
          className="text-blue-500 hover:text-blue-700 text-sm"
        >
          Download PDF
        </button>
      </div>
      <div className="w-full h-[700px]">
        {pdfBlob && (
          <iframe
            ref={iframeRef}
            src={pdfBlob}
            title={title}
            className="w-full h-full"
            allowFullScreen
          />
        )}
      </div>
    </div>
  );
};

export default PDFViewer;