import React, { useState } from 'react';
import { useData } from '../context/DataContext';
import { Download, FileText, Database, Code, CheckCircle, FileSpreadsheet, FileCode } from 'lucide-react';

const ExportPage = () => {
  const { 
    metadata, 
    mlResults, 
    loading,
    exportCleanedDataset, 
    generateReport, 
    exportMLSplits,
    exportPipeline,
    generateInferenceScript 
  } = useData();

  const [activeAction, setActiveAction] = useState(null);

  if (!metadata) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <Download className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Aucun dataset chargé
          </h3>
          <p className="text-yellow-700">
            Chargez un dataset depuis la page Import pour accéder aux exports et rapports.
          </p>
        </div>
      </div>
    );
  }

  const handleExportCleaned = async (format) => {
    setActiveAction(`cleaned_${format}`);
    try {
      await exportCleanedDataset('dataset_prepare', format);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setActiveAction(null);
    }
  };

  const handleGenerateReport = async (format) => {
    setActiveAction(`report_${format}`);
    try {
      await generateReport('rapport_audit_preparation', format);
    } catch (err) {
      console.error('Report generation failed:', err);
    } finally {
      setActiveAction(null);
    }
  };

  const handleExportMLSplits = async (format = 'csv', splitName = null) => {
    setActiveAction(`splits_${splitName || 'all'}_${format}`);
    try {
      await exportMLSplits('ml_data', format, splitName);
    } catch (err) {
      console.error('ML splits export failed:', err);
    } finally {
      setActiveAction(null);
    }
  };

  const handleExportPipeline = async () => {
    setActiveAction('pipeline');
    try {
      await exportPipeline('pipeline_entrainee.joblib');
    } catch (err) {
      console.error('Pipeline export failed:', err);
    } finally {
      setActiveAction(null);
    }
  };

  const handleGenerateInferenceScript = async () => {
    setActiveAction('inference');
    try {
      await generateInferenceScript('pipeline_entrainee.joblib', 'run_inference.py');
    } catch (err) {
      console.error('Inference script failed:', err);
    } finally {
      setActiveAction(null);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Centre d'Export & Rapports</h1>
        <p className="text-gray-600">Exportez vos données nettoyées, générez des rapports professionnels et préparez la mise en production</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Export Cleaned Dataset */}
        <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <Database className="w-6 h-6 text-primary" />
            <h2 className="text-xl font-semibold">1. Dataset Préparé & Nettoyé</h2>
          </div>
          <p className="text-gray-600 text-sm mb-6">
            Téléchargez le jeu de données avec toutes les imputations, suppressions d'aberrants et variables dérivées appliquées.
          </p>
          <div className="space-y-3">
            <button
              onClick={() => handleExportCleaned('csv')}
              disabled={loading}
              className="w-full px-4 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 font-medium transition-colors disabled:opacity-50"
            >
              <Download className="w-5 h-5" />
              {activeAction === 'cleaned_csv' ? 'Téléchargement...' : 'Exporter en CSV (.csv)'}
            </button>
            <button
              onClick={() => handleExportCleaned('excel')}
              disabled={loading}
              className="w-full px-4 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center justify-center gap-2 font-medium transition-colors disabled:opacity-50"
            >
              <FileSpreadsheet className="w-5 h-5" />
              {activeAction === 'cleaned_excel' ? 'Téléchargement...' : 'Exporter en Excel (.xlsx)'}
            </button>
          </div>
        </div>

        {/* Generate Report */}
        <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-6 h-6 text-primary" />
            <h2 className="text-xl font-semibold">2. Rapports d'Audit & Méthodologie</h2>
          </div>
          <p className="text-gray-600 text-sm mb-6">
            Rapport complet traçant l'audit de qualité, chaque décision d'imputation et les caractéristiques générées.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={() => handleGenerateReport('html')}
              disabled={loading}
              className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 text-sm font-medium transition-colors disabled:opacity-50"
            >
              <FileCode className="w-4 h-4" />
              {activeAction === 'report_html' ? 'Génération...' : 'Rapport Web (HTML)'}
            </button>
            <button
              onClick={() => handleGenerateReport('excel')}
              disabled={loading}
              className="px-4 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center justify-center gap-2 text-sm font-medium transition-colors disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" />
              {activeAction === 'report_excel' ? 'Génération...' : 'Rapport Excel (.xlsx)'}
            </button>
            <button
              onClick={() => handleGenerateReport('word')}
              disabled={loading}
              className="px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center justify-center gap-2 text-sm font-medium transition-colors disabled:opacity-50"
            >
              <FileText className="w-4 h-4" />
              {activeAction === 'report_word' ? 'Génération...' : 'Rapport Word (.docx)'}
            </button>
            <button
              onClick={() => handleGenerateReport('markdown')}
              disabled={loading}
              className="px-4 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-800 flex items-center justify-center gap-2 text-sm font-medium transition-colors disabled:opacity-50"
            >
              <FileText className="w-4 h-4" />
              {activeAction === 'report_markdown' ? 'Génération...' : 'Rapport Markdown (.md)'}
            </button>
          </div>
        </div>

        {/* ML Splits */}
        {mlResults ? (
          <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <Code className="w-6 h-6 text-primary" />
              <h2 className="text-xl font-semibold">3. Splits Train / Test ML</h2>
            </div>
            <p className="text-gray-600 text-sm mb-4">
              Ensembles d'apprentissage et de test transformés et prêts pour vos modèles.
            </p>
            <div className="grid grid-cols-2 gap-2 mb-3">
              <button
                onClick={() => handleExportMLSplits('csv', 'X_train')}
                disabled={loading}
                className="px-3 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded border border-blue-200 text-xs font-semibold flex items-center justify-center gap-1"
              >
                <Download className="w-3.5 h-3.5" />
                X_train (CSV)
              </button>
              <button
                onClick={() => handleExportMLSplits('csv', 'X_test')}
                disabled={loading}
                className="px-3 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded border border-blue-200 text-xs font-semibold flex items-center justify-center gap-1"
              >
                <Download className="w-3.5 h-3.5" />
                X_test (CSV)
              </button>
              <button
                onClick={() => handleExportMLSplits('csv', 'y_train')}
                disabled={loading}
                className="px-3 py-2 bg-purple-50 text-purple-700 hover:bg-purple-100 rounded border border-purple-200 text-xs font-semibold flex items-center justify-center gap-1"
              >
                <Download className="w-3.5 h-3.5" />
                y_train (CSV)
              </button>
              <button
                onClick={() => handleExportMLSplits('csv', 'y_test')}
                disabled={loading}
                className="px-3 py-2 bg-purple-50 text-purple-700 hover:bg-purple-100 rounded border border-purple-200 text-xs font-semibold flex items-center justify-center gap-1"
              >
                <Download className="w-3.5 h-3.5" />
                y_test (CSV)
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleExportMLSplits('csv')}
                disabled={loading}
                className="flex-1 px-4 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-gray-900 text-xs font-medium flex items-center justify-center gap-1.5"
              >
                <Download className="w-4 h-4" />
                {activeAction === 'splits_all_csv' ? 'Téléchargement...' : 'Tous les splits (ZIP)'}
              </button>
              <button
                onClick={() => handleExportMLSplits('excel')}
                disabled={loading}
                className="flex-1 px-4 py-2.5 bg-emerald-700 text-white rounded-lg hover:bg-emerald-800 text-xs font-medium flex items-center justify-center gap-1.5"
              >
                <FileSpreadsheet className="w-4 h-4" />
                {activeAction === 'splits_all_excel' ? 'Téléchargement...' : 'Classeur Excel'}
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg border border-dashed border-gray-300 p-6 flex flex-col justify-center items-center text-center">
            <Code className="w-8 h-8 text-gray-400 mb-2" />
            <h3 className="font-medium text-gray-700">Splits Machine Learning</h3>
            <p className="text-xs text-gray-500 max-w-xs mt-1">
              Configurez une cible et un pipeline dans l'onglet Machine Learning pour activer l'export des jeux train/test.
            </p>
          </div>
        )}

        {/* Pipeline Export */}
        {mlResults ? (
          <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <Code className="w-6 h-6 text-primary" />
              <h2 className="text-xl font-semibold">4. Déploiement en Production</h2>
            </div>
            <p className="text-gray-600 text-sm mb-6">
              Exportez la pipeline Scikit-Learn ajustée et le script d'inférence autonome pour transformer de nouvelles données.
            </p>
            <div className="space-y-3">
              <button
                onClick={handleExportPipeline}
                disabled={loading}
                className="w-full px-4 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 font-medium transition-colors disabled:opacity-50"
              >
                <Download className="w-5 h-5" />
                {activeAction === 'pipeline' ? 'Téléchargement...' : 'Exporter pipeline Scikit-Learn (.joblib)'}
              </button>
              <button
                onClick={handleGenerateInferenceScript}
                disabled={loading}
                className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-800 flex items-center justify-center gap-2 font-medium transition-colors disabled:opacity-50"
              >
                <FileCode className="w-5 h-5" />
                {activeAction === 'inference' ? 'Génération...' : "Télécharger le script d'inférence (run_inference.py)"}
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg border border-dashed border-gray-300 p-6 flex flex-col justify-center items-center text-center">
            <CheckCircle className="w-8 h-8 text-gray-400 mb-2" />
            <h3 className="font-medium text-gray-700">Pipeline de Production</h3>
            <p className="text-xs text-gray-500 max-w-xs mt-1">
              La sérialisation joblib et le script d'inférence seront disponibles après configuration du pipeline ML.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExportPage;
