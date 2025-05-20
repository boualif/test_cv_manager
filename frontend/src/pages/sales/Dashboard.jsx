import React from 'react';
import Sidebar from '../../components/Sidebar';

const SalesDashboard = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Sidebar />
      <div className="md:ml-64 container mx-auto p-6 flex-grow">
        <h1 className="text-2xl font-bold mb-6">Tableau de bord Commercial</h1>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <p>Bienvenue sur votre tableau de bord commercial. Vous pouvez consulter les informations des candidats liées aux ventes ici.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <h3 className="text-lg font-semibold text-blue-800 mb-2">Opportunités récentes</h3>
              <p className="text-gray-600">Consultez et gérez vos opportunités commerciales actuelles.</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-100">
              <h3 className="text-lg font-semibold text-green-800 mb-2">Prospects</h3>
              <p className="text-gray-600">Accédez à la liste de vos prospects et suivez leur statut.</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
              <h3 className="text-lg font-semibold text-purple-800 mb-2">Activités récentes</h3>
              <p className="text-gray-600">Visualisez vos dernières activités commerciales.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SalesDashboard;