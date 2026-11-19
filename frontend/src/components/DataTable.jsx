import React, { useState, useEffect } from 'react';
import { useData } from '../context/DataContext';

const DataTable = () => {
  const { getPreview, metadata } = useData();
  const [previewData, setPreviewData] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 50;

  useEffect(() => {
    if (metadata) {
      loadPreview(0);
    }
  }, [metadata]);

  const loadPreview = async (page) => {
    try {
      const data = await getPreview(page, pageSize);
      setPreviewData(data);
      setCurrentPage(page);
    } catch (err) {
      console.error('Error loading preview:', err);
    }
  };

  if (!previewData || !previewData.data) {
    return (
      <div className="bg-card rounded-lg border border-gray-200 p-8 text-center text-gray-500">
        Aucune donnée à afficher. Chargez un dataset d'abord.
      </div>
    );
  }

  const totalPages = previewData.total_pages;
  const startRow = currentPage * pageSize + 1;
  const endRow = Math.min((currentPage + 1) * pageSize, previewData.total_rows);

  return (
    <div className="bg-card rounded-lg border border-gray-200 overflow-hidden">
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Aperçu des données</h3>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>
            Lignes {startRow} - {endRow} sur {previewData.total_rows}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              {previewData.columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-b border-gray-200"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {previewData.data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {previewData.columns.map((col) => (
                  <td key={col} className="px-4 py-3 text-sm text-gray-700">
                    {row[col] !== null && row[col] !== undefined ? String(row[col]) : '<NA>'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <button
          onClick={() => loadPreview(currentPage - 1)}
          disabled={currentPage === 0}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Précédent
        </button>
        <span className="text-sm text-gray-600">
          Page {currentPage + 1} sur {totalPages}
        </span>
        <button
          onClick={() => loadPreview(currentPage + 1)}
          disabled={currentPage >= totalPages - 1}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Suivant
        </button>
      </div>
    </div>
  );
};

export default DataTable;
