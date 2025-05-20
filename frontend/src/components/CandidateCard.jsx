import React from 'react';
import { Link } from 'react-router-dom';

const CandidateCard = ({ candidate }) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
      <h3 className="font-bold text-lg text-gray-800">{candidate.name}</h3>
      <p className="text-gray-600 mb-1">{candidate.job_title}</p>
      <p className="text-sm text-gray-500 mb-3">{candidate.email}</p>
      <p className="text-sm text-gray-400 mb-3">Added {new Date(candidate.created_at).toLocaleDateString()}</p>
      
      <Link
        to={`api/candidates/${candidate.id}`}
        className="text-blue-500 hover:text-blue-700 text-sm font-medium flex items-center"
      >
        View Profile
        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </Link>
    </div>
  );
};

export default CandidateCard;