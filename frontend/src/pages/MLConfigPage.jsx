import React, { useState, useEffect } from 'react';
import { useData } from '../context/DataContext';
import { Cpu, AlertTriangle } from 'lucide-react';

const MLConfigPage = () => {
  const { metadata, mlResults, buildSupervisedPipeline } = useData();
  const [mode, setMode] = useState('supervised');
  const [targetCol, setTargetCol] = useState('');
  const [testSize, setTestSize] = useState(0.2);
  const [splitStrategy, setSplitStrategy] = useState('stratified');
  const [numericScaler, setNumericScaler] = useState('standard');
  const [categoricalEncoder, setCategoricalEncoder] = useState('onehot');

  useEffect(() => {
    if (metadata?.columns) {
      setTargetCol(metadata.columns[metadata.columns.length - 1]);
    }
  }, [metadata]);

  if (!metadata) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <Cpu className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Aucun dataset chargé
          </h3>
          <p className="text-yellow-700">
            Chargez un dataset depuis la page Import pour configurer le ML.
          </p>
        </div>
      </div>
    );
  }

  const handleBuildPipeline = async () => {
    try {
      await buildSupervisedPipeline({
        target_col: targetCol,
        test_size: testSize,
        split_strategy: splitStrategy,
        numeric_scaler: numericScaler,
        categorical_encoder: categoricalEncoder,
      });
    } catch (err) {
      console.error('Pipeline build failed:', err);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Configuration Machine Learning</h1>
        <p className="text-gray-600">Préparation des données avec garantie zéro fuite</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Configuration Panel */}
        <div className="bg-card rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-6">Paramètres</h2>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mode
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              >
                <option value="supervised">Supervisé</option>
                <option value="unsupervised">Non supervisé</option>
              </select>
            </div>

            {mode === 'supervised' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Variable cible
                  </label>
                  <select
                    value={targetCol}
                    onChange={(e) => setTargetCol(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    {metadata.columns.map((col) => (
                      <option key={col} value={col}>
                        {col}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Proportion de test: {testSize * 100}%
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="0.5"
                    step="0.05"
                    value={testSize}
                    onChange={(e) => setTestSize(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Stratégie de split
                  </label>
                  <select
                    value={splitStrategy}
                    onChange={(e) => setSplitStrategy(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="stratified">Stratifié</option>
                    <option value="random">Aléatoire</option>
                    <option value="chronological">Chronologique</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mise à l'échelle numérique
                  </label>
                  <select
                    value={numericScaler}
                    onChange={(e) => setNumericScaler(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="standard">StandardScaler</option>
                    <option value="minmax">MinMaxScaler</option>
                    <option value="robust">RobustScaler</option>
                    <option value="none">Aucun</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Encodage catégoriel
                  </label>
                  <select
                    value={categoricalEncoder}
                    onChange={(e) => setCategoricalEncoder(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="onehot">One-Hot Encoding</option>
                    <option value="ordinal">Ordinal Encoding</option>
                    <option value="none">Aucun</option>
                  </select>
                </div>
              </>
            )}

            <button
              onClick={handleBuildPipeline}
              className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 font-semibold"
            >
              Générer Pipeline & Préparer les Données
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="bg-card rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-6">Résultats</h2>

          {!mlResults ? (
            <p className="text-gray-500 text-center py-8">
              Configurez et lancez la préparation pour voir les résultats.
            </p>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="font-medium text-blue-900">Tâche détectée</p>
                <p className="text-blue-700">{mlResults.task_type}</p>
              </div>

              {mlResults.X_train_shape && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="font-medium text-green-900">Dimensions Train</p>
                  <p className="text-green-700">{mlResults.X_train_shape[0]} lignes × {mlResults.X_train_shape[1]} variables</p>
                </div>
              )}

              {mlResults.X_test_shape && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="font-medium text-green-900">Dimensions Test</p>
                  <p className="text-green-700">{mlResults.X_test_shape[0]} lignes × {mlResults.X_test_shape[1]} variables</p>
                </div>
              )}

              {mlResults.leakage_warnings && mlResults.leakage_warnings.length > 0 && (
                <div className="p-4 bg-red-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                    <p className="font-medium text-red-900">Avertissements de fuite de données</p>
                  </div>
                  <ul className="text-sm text-red-700 space-y-1">
                    {mlResults.leakage_warnings.map((warning, idx) => (
                      <li key={idx}>• {warning.column}: {warning.reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              {mlResults.recommended_models && (
                <div>
                  <p className="font-medium text-gray-900 mb-2">Algorithmes recommandés</p>
                  <div className="space-y-2">
                    {mlResults.recommended_models.map((model, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded">
                        <p className="font-medium text-gray-900">{model.name}</p>
                        <p className="text-sm text-gray-600">{model.notes}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MLConfigPage;
