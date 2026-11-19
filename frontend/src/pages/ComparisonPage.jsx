import React, { useState, useEffect } from 'react';
import { useData } from '../context/DataContext';
import { ArrowLeftRight, Database, AlertCircle, CheckCircle } from 'lucide-react';

const ComparisonPage = () => {
  const { metadata, compareBeforeAfter, cleaningHistory } = useData();
  const [comparisonData, setComparisonData] = useState(null);
  const [selectedColumn, setSelectedColumn] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (metadata) {
      fetchComparison();
    }
  }, [metadata, cleaningHistory]);

  const fetchComparison = async () => {
    try {
      setLoading(true);
      const data = await compareBeforeAfter(selectedColumn || null);
      setComparisonData(data);
    } catch (err) {
      console.error('Failed to fetch comparison:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleColumnChange = (e) => {
    setSelectedColumn(e.target.value);
  };

  const handleCompare = () => {
    fetchComparison();
  };

  if (!metadata) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <Database className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Aucune donnée disponible
          </h3>
          <p className="text-yellow-700">
            Importez un dataset pour voir la comparaison avant/après.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Comparaison Avant/Après</h1>
        <p className="text-gray-600">Visualisez l'impact des opérations de nettoyage</p>
      </div>

      {/* Controls */}
      <div className="mb-6 bg-card rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sélectionner une colonne (optionnel)
            </label>
            <select
              value={selectedColumn}
              onChange={handleColumnChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Dataset entier</option>
              {metadata.columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleCompare}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <ArrowLeftRight className="w-4 h-4" />
              {loading ? 'Comparaison...' : 'Comparer'}
            </button>
          </div>
        </div>
      </div>

      {/* Comparison Results */}
      {comparisonData && (
        <div className="space-y-6">
          {/* Dataset-level comparison */}
          {!selectedColumn && comparisonData.original && (
            <div className="bg-card rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Database className="w-5 h-5" />
                Comparaison Globale du Dataset
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Original Stats */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">État Original</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Lignes:</span>
                      <span className="font-medium">{comparisonData.original.rows}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Colonnes:</span>
                      <span className="font-medium">{comparisonData.original.cols}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Valeurs manquantes:</span>
                      <span className="font-medium">{comparisonData.original.total_missing}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Doublons:</span>
                      <span className="font-medium">{comparisonData.original.duplicate_rows}</span>
                    </div>
                  </div>
                </div>

                {/* Current Stats */}
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">État Actuel</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Lignes:</span>
                      <span className="font-medium">{comparisonData.current.rows}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Colonnes:</span>
                      <span className="font-medium">{comparisonData.current.cols}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Valeurs manquantes:</span>
                      <span className="font-medium">{comparisonData.current.total_missing}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Doublons:</span>
                      <span className="font-medium">{comparisonData.current.duplicate_rows}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Changes Summary */}
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Résumé des Changements
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Lignes supprimées</p>
                    <p className="font-semibold text-lg">{comparisonData.changes.rows_removed}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Colonnes supprimées</p>
                    <p className="font-semibold text-lg">{comparisonData.changes.cols_removed}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Manquantes résolues</p>
                    <p className="font-semibold text-lg">{comparisonData.changes.missing_resolved}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Doublons supprimés</p>
                    <p className="font-semibold text-lg">{comparisonData.changes.duplicates_removed}</p>
                  </div>
                </div>
              </div>

              {/* Operations Applied */}
              {comparisonData.operations_applied > 0 && (
                <div className="mt-6">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Opérations Appliquées ({comparisonData.operations_applied})
                  </h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {comparisonData.operations.map((op, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded text-sm">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium">{op.operation}</p>
                            <p className="text-gray-600 text-xs">{op.column}</p>
                          </div>
                          <span className="text-xs text-gray-500">{op.timestamp}</span>
                        </div>
                        <p className="text-gray-600 mt-1">{op.details}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Column-level comparison */}
          {selectedColumn && comparisonData.column && (
            <div className="bg-card rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Database className="w-5 h-5" />
                Comparaison: {selectedColumn}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Original Stats */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">Original</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="font-medium">{comparisonData.original.dtype}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Manquantes:</span>
                      <span className="font-medium">{comparisonData.original.missing_count} ({comparisonData.original.missing_pct}%)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Distinctes:</span>
                      <span className="font-medium">{comparisonData.original.unique_count}</span>
                    </div>
                    {comparisonData.original.mean !== undefined && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Moyenne:</span>
                          <span className="font-medium">{comparisonData.original.mean.toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Écart-type:</span>
                          <span className="font-medium">{comparisonData.original.std.toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Min/Max:</span>
                          <span className="font-medium">{comparisonData.original.min.toFixed(4)} / {comparisonData.original.max.toFixed(4)}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Current Stats */}
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-3">Actuel</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="font-medium">{comparisonData.current.dtype}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Manquantes:</span>
                      <span className="font-medium">{comparisonData.current.missing_count} ({comparisonData.current.missing_pct}%)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Distinctes:</span>
                      <span className="font-medium">{comparisonData.current.unique_count}</span>
                    </div>
                    {comparisonData.current.mean !== undefined && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Moyenne:</span>
                          <span className="font-medium">{comparisonData.current.mean.toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Écart-type:</span>
                          <span className="font-medium">{comparisonData.current.std.toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Min/Max:</span>
                          <span className="font-medium">{comparisonData.current.min.toFixed(4)} / {comparisonData.current.max.toFixed(4)}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Changes */}
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Changements
                </h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Lignes changées</p>
                    <p className="font-semibold text-lg">{comparisonData.changes.rows_changed}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Manquantes changées</p>
                    <p className="font-semibold text-lg">{comparisonData.changes.missing_change}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Distinctes changées</p>
                    <p className="font-semibold text-lg">{comparisonData.changes.unique_change}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ComparisonPage;
