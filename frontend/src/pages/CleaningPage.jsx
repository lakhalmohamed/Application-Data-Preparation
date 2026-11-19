import React, { useState, useEffect } from 'react';
import { useData } from '../context/DataContext';
import { Sparkles, Undo, RotateCcw, Trash2, Type, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const CleaningPage = () => {
  const { 
    metadata, 
    cleaningHistory, 
    loading, 
    imputeMissing, 
    handleOutliers, 
    cleanText,
    removeDuplicates,
    dropColumns,
    undoLastOperation,
    resetDataset,
    refreshHistoryAndMetadata
  } = useData();

  const [activeTab, setActiveTab] = useState('impute');
  const [selectedColumn, setSelectedColumn] = useState('');
  const [imputeStrategy, setImputeStrategy] = useState('mean');
  const [imputeConstantVal, setImputeConstantVal] = useState('Inconnu');
  const [outlierMethod, setOutlierMethod] = useState('iqr');
  const [outlierAction, setOutlierAction] = useState('clip');
  const [textCasing, setTextCasing] = useState('lower');
  const [textStrip, setTextStrip] = useState(true);
  const [colsToDrop, setColsToDrop] = useState([]);

  useEffect(() => {
    if (metadata?.columns?.length > 0 && !selectedColumn) {
      setSelectedColumn(metadata.columns[0]);
    }
  }, [metadata, selectedColumn]);

  useEffect(() => {
    refreshHistoryAndMetadata();
  }, [refreshHistoryAndMetadata]);

  if (!metadata) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <Sparkles className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Aucun dataset chargé
          </h3>
          <p className="text-yellow-700">
            Chargez un dataset depuis la page Import pour accéder au nettoyage.
          </p>
        </div>
      </div>
    );
  }

  const handleImpute = async () => {
    try {
      const fillVal = imputeStrategy === 'constant' ? imputeConstantVal : null;
      await imputeMissing(selectedColumn, imputeStrategy, fillVal);
    } catch (err) {
      console.error('Imputation failed:', err);
    }
  };

  const handleOutlierTreatment = async () => {
    try {
      await handleOutliers(selectedColumn, outlierMethod, outlierAction);
    } catch (err) {
      console.error('Outlier treatment failed:', err);
    }
  };

  const handleCleanText = async () => {
    try {
      await cleanText(selectedColumn, {
        casing: textCasing,
        strip: textStrip,
        emptyToNan: true
      });
    } catch (err) {
      console.error('Text cleaning failed:', err);
    }
  };

  const handleRemoveDuplicates = async () => {
    try {
      await removeDuplicates();
    } catch (err) {
      console.error('Duplicate removal failed:', err);
    }
  };

  const handleDropColumns = async () => {
    if (colsToDrop.length === 0) return;
    try {
      await dropColumns(colsToDrop);
      setColsToDrop([]);
    } catch (err) {
      console.error('Drop columns failed:', err);
    }
  };

  const handleUndo = async () => {
    try {
      await undoLastOperation();
    } catch (err) {
      console.error('Undo failed:', err);
    }
  };

  const handleReset = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir réinitialiser toutes les opérations de nettoyage ?')) {
      try {
        await resetDataset();
      } catch (err) {
        console.error('Reset failed:', err);
      }
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Nettoyage des Données</h1>
        <p className="text-gray-600">Imputation intelligente, traitement des outliers, normalisation textuelle et gestion des doublons</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Panel: Operations */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="border-b border-gray-200 bg-gray-50/50">
              <nav className="flex flex-wrap">
                {[
                  { id: 'impute', label: 'Imputation' },
                  { id: 'outliers', label: 'Outliers' },
                  { id: 'text', label: 'Texte' },
                  { id: 'duplicates', label: 'Doublons' },
                  { id: 'drop', label: 'Suppression Colonnes' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-5 py-3.5 font-medium text-sm transition-colors ${
                      activeTab === tab.id
                        ? 'border-b-2 border-primary text-primary bg-white'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            <div className="p-6">
              {/* TAB: IMPUTE */}
              {activeTab === 'impute' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Colonne à imputer
                    </label>
                    <select
                      value={selectedColumn}
                      onChange={(e) => setSelectedColumn(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      {metadata.columns.map((col) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Stratégie d'imputation
                    </label>
                    <select
                      value={imputeStrategy}
                      onChange={(e) => setImputeStrategy(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="mean">Moyenne (numérique continu symétrique)</option>
                      <option value="median">Médiane (numérique avec valeurs extrêmes)</option>
                      <option value="mode">Mode (catégorie la plus fréquente)</option>
                      <option value="constant">Valeur constante personnalisée</option>
                      <option value="forward_fill">Propagation avant (forward fill)</option>
                      <option value="backward_fill">Propagation arrière (backward fill)</option>
                      <option value="knn">KNN Imputation (k plus proches voisins)</option>
                      <option value="drop_rows">Supprimer les lignes avec valeurs manquantes</option>
                    </select>
                  </div>

                  {imputeStrategy === 'constant' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Valeur constante de remplacement
                      </label>
                      <input
                        type="text"
                        value={imputeConstantVal}
                        onChange={(e) => setImputeConstantVal(e.target.value)}
                        placeholder="Inconnu, 0, N/A..."
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                      />
                    </div>
                  )}

                  <button
                    onClick={handleImpute}
                    disabled={loading || !selectedColumn}
                    className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors flex items-center justify-center gap-2 shadow-sm"
                  >
                    <Sparkles className="w-5 h-5" />
                    {loading ? 'Traitement en cours...' : 'Appliquer l\'imputation'}
                  </button>
                </div>
              )}

              {/* TAB: OUTLIERS */}
              {activeTab === 'outliers' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Colonne numérique
                    </label>
                    <select
                      value={selectedColumn}
                      onChange={(e) => setSelectedColumn(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      {metadata.columns.map((col) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Méthode de détection
                    </label>
                    <select
                      value={outlierMethod}
                      onChange={(e) => setOutlierMethod(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="iqr">IQR (Écart interquartile, 1.5 × IQR)</option>
                      <option value="zscore">Z-Score (Score standardisé |z| &gt; 3)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Action corrective
                    </label>
                    <select
                      value={outlierAction}
                      onChange={(e) => setOutlierAction(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="clip">Écrêtage / Winsorisation (Capping aux bornes min/max)</option>
                      <option value="nan">Convertir en NaN (à imputer ensuite)</option>
                      <option value="drop">Supprimer les lignes aberrantes</option>
                    </select>
                  </div>

                  <button
                    onClick={handleOutlierTreatment}
                    disabled={loading || !selectedColumn}
                    className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors shadow-sm"
                  >
                    {loading ? 'Traitement...' : 'Traiter les valeurs aberrantes'}
                  </button>
                </div>
              )}

              {/* TAB: TEXT */}
              {activeTab === 'text' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Colonne textuelle
                    </label>
                    <select
                      value={selectedColumn}
                      onChange={(e) => setSelectedColumn(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      {metadata.columns.map((col) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Harmonisation de la casse
                    </label>
                    <select
                      value={textCasing}
                      onChange={(e) => setTextCasing(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="lower">Minuscules (ex: mad / france)</option>
                      <option value="upper">Majuscules (ex: MAD / FRANCE)</option>
                      <option value="title">Casse Titre (ex: Mad / France)</option>
                    </select>
                  </div>

                  <label className="flex items-center gap-2 cursor-pointer bg-gray-50 p-3 rounded-lg border">
                    <input
                      type="checkbox"
                      checked={textStrip}
                      onChange={(e) => setTextStrip(e.target.checked)}
                      className="rounded text-primary focus:ring-primary"
                    />
                    <span className="text-sm text-gray-700">
                      Supprimer les espaces superflus en début et fin de chaîne (trim)
                    </span>
                  </label>

                  <button
                    onClick={handleCleanText}
                    disabled={loading || !selectedColumn}
                    className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors shadow-sm"
                  >
                    {loading ? 'Nettoyage...' : 'Normaliser la colonne textuelle'}
                  </button>
                </div>
              )}

              {/* TAB: DUPLICATES */}
              {activeTab === 'duplicates' && (
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                    Détecte et supprime les doublons complets ligne par ligne tout en conservant la première occurrence unique.
                  </div>
                  <button
                    onClick={handleRemoveDuplicates}
                    disabled={loading}
                    className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 font-medium transition-colors shadow-sm"
                  >
                    <Trash2 className="w-5 h-5" />
                    {loading ? 'Traitement...' : 'Détecter & supprimer les doublons'}
                  </button>
                </div>
              )}

              {/* TAB: DROP */}
              {activeTab === 'drop' && (
                <div className="space-y-4">
                  <p className="text-sm text-gray-600">
                    Sélectionnez les colonnes à supprimer définitivement du dataset (identifiants, colonnes vides, etc.) :
                  </p>
                  <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-3 space-y-2 bg-gray-50">
                    {metadata.columns.map((col) => (
                      <label key={col} className="flex items-center gap-2 cursor-pointer text-sm">
                        <input
                          type="checkbox"
                          checked={colsToDrop.includes(col)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setColsToDrop([...colsToDrop, col]);
                            } else {
                              setColsToDrop(colsToDrop.filter((c) => c !== col));
                            }
                          }}
                          className="rounded text-red-600 focus:ring-red-500"
                        />
                        <span className="text-gray-800">{col}</span>
                      </label>
                    ))}
                  </div>
                  <button
                    onClick={handleDropColumns}
                    disabled={loading || colsToDrop.length === 0}
                    className="w-full px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-5 h-5" />
                    {loading ? 'Suppression...' : `Supprimer ${colsToDrop.length} colonne(s)`}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons: Undo / Reset */}
          <div className="flex gap-4">
            <button
              onClick={handleUndo}
              disabled={loading || cleaningHistory.length === 0}
              className="flex-1 px-6 py-3 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm transition-colors"
            >
              <Undo className="w-5 h-5 text-gray-600" />
              Annuler la dernière opération
            </button>
            <button
              onClick={handleReset}
              disabled={loading || cleaningHistory.length === 0}
              className="flex-1 px-6 py-3 bg-red-50 border border-red-200 text-red-700 font-medium rounded-lg hover:bg-red-100 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
            >
              <RotateCcw className="w-5 h-5 text-red-600" />
              Réinitialiser le dataset
            </button>
          </div>
        </div>

        {/* Right Panel: Operations Journal */}
        <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4 pb-2 border-b">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Journal d'opérations
            </h2>
            <span className="text-xs bg-blue-100 text-primary font-semibold px-2 py-0.5 rounded-full">
              {cleaningHistory.length}
            </span>
          </div>

          {cleaningHistory.length === 0 ? (
            <div className="py-12 text-center text-gray-400 space-y-2">
              <Sparkles className="w-8 h-8 mx-auto text-gray-300" />
              <p className="text-sm">Aucune opération effectuée.</p>
              <p className="text-xs text-gray-400">Vos actions d'imputation, filtres et transformations s'afficheront ici.</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {cleaningHistory.map((op, idx) => (
                <div key={idx} className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs space-y-1 hover:border-gray-300 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-900 bg-white px-2 py-0.5 rounded border border-gray-200">
                      {op.operation}
                    </span>
                    <span className="text-[10px] text-gray-400">{op.timestamp}</span>
                  </div>
                  <p className="text-gray-700 font-medium">
                    Colonne : <span className="font-semibold text-primary">{op.column}</span>
                  </p>
                  {op.strategy && (
                    <p className="text-gray-500">
                      Stratégie : <span className="italic">{op.strategy}</span>
                    </p>
                  )}
                  <p className="text-gray-600 pt-0.5">{op.details}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CleaningPage;
