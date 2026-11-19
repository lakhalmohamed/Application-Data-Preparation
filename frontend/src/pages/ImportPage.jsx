import React, { useState } from 'react';
import { useData } from '../context/DataContext';
import { Upload, FileText, Database, AlertCircle, Target } from 'lucide-react';
import KPICard from '../components/KPICard';
import DataTable from '../components/DataTable';

const ImportPage = () => {
  const { uploadDataset, metadata, loading, runAnalysis, selectTargetVariable, analysisResults } = useData();
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [csvParams, setCsvParams] = useState({
    delimiter: '',
    encoding: '',
    decimal: '',
  });
  const [targetColumn, setTargetColumn] = useState('');
  const [learningMode, setLearningMode] = useState('supervised');
  const [targetInfo, setTargetInfo] = useState(null);

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
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    try {
      await uploadDataset(file, csvParams);
      setFile(null);
      setCsvParams({ delimiter: '', encoding: '', decimal: '' });
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  const handleRunAnalysis = async () => {
    try {
      await runAnalysis();
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  const handleSelectTarget = async () => {
    try {
      const result = await selectTargetVariable(targetColumn, learningMode);
      setTargetInfo(result);
    } catch (err) {
      console.error('Target selection failed:', err);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Importation & Gestion du Dataset</h1>
        <p className="text-gray-600">Chargez votre fichier pour commencer l'analyse</p>
      </div>

      {/* Upload Section */}
      <div className="mb-8">
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
            dragActive
              ? 'border-primary bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-700 mb-2">
            Glissez-déposez votre fichier ici
          </p>
          <p className="text-gray-500 mb-4">ou</p>
          <label className="inline-flex items-center px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
            <FileText className="w-5 h-5 mr-2" />
            Parcourir les fichiers
            <input
              type="file"
              className="hidden"
              onChange={handleChange}
              accept=".csv,.xlsx,.xls,.json,.parquet,.tsv,.txt"
            />
          </label>
          <p className="text-sm text-gray-500 mt-4">
            Formats supportés: CSV, Excel, JSON, Parquet, TSV
          </p>
        </div>

        {file && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-primary" />
              <span className="font-medium text-gray-700">{file.name}</span>
              <span className="text-sm text-gray-500">({(file.size / 1024).toFixed(2)} KB)</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <select
                  value={csvParams.delimiter}
                  onChange={(e) => setCsvParams({ ...csvParams, delimiter: e.target.value })}
                  className="px-3 py-1 border rounded text-sm"
                >
                  <option value="">Séparateur auto</option>
                  <option value=",">Virgule (,)</option>
                  <option value=";">Point-virgule (;)</option>
                  <option value="\t">Tabulation</option>
                  <option value="|">Pipe (|)</option>
                </select>
                <select
                  value={csvParams.encoding}
                  onChange={(e) => setCsvParams({ ...csvParams, encoding: e.target.value })}
                  className="px-3 py-1 border rounded text-sm"
                >
                  <option value="">Encodage auto</option>
                  <option value="utf-8">UTF-8</option>
                  <option value="latin-1">Latin-1</option>
                  <option value="cp1252">CP1252</option>
                </select>
                <select
                  value={csvParams.decimal}
                  onChange={(e) => setCsvParams({ ...csvParams, decimal: e.target.value })}
                  className="px-3 py-1 border rounded text-sm"
                >
                  <option value="">Décimal auto</option>
                  <option value=".">Point (.)</option>
                  <option value=",">Virgule (,)</option>
                </select>
              </div>
              <button
                onClick={handleUpload}
                disabled={loading}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Chargement...' : 'Charger'}
              </button>
              <button
                onClick={() => setFile(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Annuler
              </button>
            </div>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      {metadata && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
            <KPICard title="Fichier" value={metadata.file_name} icon={FileText} />
            <KPICard title="Format" value={`${metadata.format} (${metadata.encoding})`} icon={Database} />
            <KPICard title="Dimensions" value={`${metadata.rows} × ${metadata.cols}`} />
            <KPICard title="Manquantes" value={`${metadata.total_missing} (${metadata.missing_pct}%)`} icon={AlertCircle} />
            <KPICard title="Doublons" value={`${metadata.duplicate_rows} (${metadata.duplicate_pct}%)`} icon={AlertCircle} />
            <KPICard title="Mémoire" value={metadata.memory_formatted} icon={Database} />
          </div>

          {/* Data Preview */}
          <div className="mb-8">
            <DataTable />
          </div>

          {/* Target Variable Selection */}
          {metadata && (
            <div className="mb-8 bg-card rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5" />
                Configuration Machine Learning
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mode d'apprentissage
                  </label>
                  <select
                    value={learningMode}
                    onChange={(e) => setLearningMode(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="supervised">Supervisé (avec cible)</option>
                    <option value="unsupervised">Non supervisé (sans cible)</option>
                  </select>
                </div>
                {learningMode === 'supervised' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Variable cible
                    </label>
                    <select
                      value={targetColumn}
                      onChange={(e) => setTargetColumn(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="">Sélectionner une variable...</option>
                      {metadata.columns.map((col) => (
                        <option key={col} value={col}>
                          {col}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              {learningMode === 'supervised' && targetColumn && (
                <button
                  onClick={handleSelectTarget}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Analyse en cours...' : 'Confirmer la sélection'}
                </button>
              )}
              {targetInfo && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="font-medium text-blue-900">{targetInfo.message}</p>
                  <p className="text-sm text-blue-700 mt-1">
                    Tâche détectée: <strong>{targetInfo.task_type}</strong>
                  </p>
                  {targetInfo.imbalance_info && targetInfo.imbalance_info.is_imbalanced && (
                    <p className="text-sm text-orange-700 mt-1">
                      ⚠️ {targetInfo.imbalance_info.warning}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Run Analysis Button */}
          <div className="flex justify-end">
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold disabled:opacity-50 flex items-center gap-2"
            >
              <Database className="w-5 h-5" />
              {loading ? 'Analyse en cours...' : 'Lancer l\'Analyse Intelligente Complète'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ImportPage;
