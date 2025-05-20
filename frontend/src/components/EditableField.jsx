// src/components/EditableField.jsx
import React, { useState } from 'react';

const EditableField = ({ 
  label, 
  value, 
  fieldName, 
  onSave, 
  type = 'text', 
  options = [], 
  placeholder = '' 
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  
  const handleSave = () => {
    onSave(fieldName, editValue);
    setIsEditing(false);
  };
  
  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };
  
  if (!isEditing) {
    return (
      <div className="py-2 px-3 group relative">
        <div className="flex justify-between items-center">
          <div>
            <span className="font-medium text-gray-500">{label}:</span>
            <span className="ml-2">{value || '-'}</span>
          </div>
          <button
            className="invisible group-hover:visible text-blue-500 hover:text-blue-700"
            onClick={() => setIsEditing(true)}
            title="Modifier"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
            </svg>
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="py-2 px-3 bg-blue-50 rounded">
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      
      {type === 'select' ? (
        <select
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={editValue || ''}
          onChange={(e) => setEditValue(e.target.value)}
        >
          <option value="">-- Sélectionner --</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={editValue || ''}
          placeholder={placeholder}
          onChange={(e) => setEditValue(e.target.value)}
          rows={3}
        />
      ) : (
        <input
          type={type}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={editValue || ''}
          placeholder={placeholder}
          onChange={(e) => setEditValue(e.target.value)}
        />
      )}
      
      <div className="flex justify-end mt-2 space-x-2">
        <button
          className="px-2 py-1 text-sm text-gray-600 hover:text-gray-800"
          onClick={handleCancel}
        >
          Annuler
        </button>
        <button
          className="px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          onClick={handleSave}
        >
          Enregistrer
        </button>
      </div>
    </div>
  );
};

export default EditableField;