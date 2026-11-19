import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import apiClient, { generateSessionId } from '../api/client';

const DataContext = createContext();

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};

const extractErrorMessage = async (err, defaultMsg) => {
  if (err.response?.data) {
    if (err.response.data instanceof Blob) {
      try {
        const text = await err.response.data.text();
        const json = JSON.parse(text);
        if (json.detail) return json.detail;
      } catch (e) {
        // Not a JSON blob
      }
    } else if (err.response.data.detail) {
      return err.response.data.detail;
    }
  }
  return err.message || defaultMsg;
};

export const DataProvider = ({ children }) => {
  const [sessionId] = useState(() => generateSessionId());
  const [metadata, setMetadata] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [cleaningHistory, setCleaningHistory] = useState([]);
  const [mlResults, setMlResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  const showNotification = useCallback((message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3500);
  }, []);

  const refreshHistoryAndMetadata = useCallback(async () => {
    try {
      const [historyRes, metaRes] = await Promise.all([
        apiClient.get('/api/cleaning/history', { params: { session_id: sessionId } }),
        apiClient.get('/api/dataset/metadata', { params: { session_id: sessionId } })
      ]);
      if (historyRes.data?.history) {
        setCleaningHistory(historyRes.data.history);
      }
      if (metaRes.data) {
        setMetadata(metaRes.data);
      }
    } catch (err) {
      console.warn('Could not refresh history/metadata:', err);
    }
  }, [sessionId]);

  const uploadDataset = useCallback(async (file, params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);
      if (params.delimiter) formData.append('delimiter', params.delimiter);
      if (params.encoding) formData.append('encoding', params.encoding);
      if (params.decimal) formData.append('decimal', params.decimal);

      const response = await apiClient.post('/api/dataset/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { session_id: sessionId },
      });

      setMetadata(response.data);
      setAnalysisResults(null);
      setCleaningHistory([]);
      setMlResults(null);
      showNotification('Dataset chargé avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors du chargement du dataset');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const getPreview = useCallback(async (page = 0, pageSize = 50) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/dataset/preview', {
        page,
        page_size: pageSize,
      }, { params: { session_id: sessionId } });
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de la récupération de l'aperçu");
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/analysis/run', null, {
        params: { session_id: sessionId },
      });
      setAnalysisResults(response.data);
      showNotification('Analyse terminée avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de l'analyse");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const selectTargetVariable = useCallback(async (targetColumn, learningMode = 'supervised') => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/dataset/select-target', {
        target_column: targetColumn,
        learning_mode: learningMode,
      }, { params: { session_id: sessionId } });
      showNotification('Variable cible sélectionnée avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors de la sélection de la cible');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const getCorrelationHeatmap = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/api/analysis/correlation-heatmap', {
        params: { session_id: sessionId },
      });
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur corrélation');
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const compareBeforeAfter = useCallback(async (column = null) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/analysis/compare', {
        column,
      }, { params: { session_id: sessionId } });
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors de la comparaison avant/après');
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const imputeMissing = useCallback(async (column, strategy, fillValue = null) => {
    setLoading(true);
    try {
      await apiClient.post('/api/cleaning/impute', {
        column,
        strategy,
        fill_value: fillValue,
      }, { params: { session_id: sessionId } });
      
      await refreshHistoryAndMetadata();
      showNotification('Imputation réussie');
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de l'imputation");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const handleOutliers = useCallback(async (column, method, action, threshold = 1.5) => {
    setLoading(true);
    try {
      await apiClient.post('/api/cleaning/outliers', {
        column,
        method,
        action,
        threshold,
      }, { params: { session_id: sessionId } });
      
      await refreshHistoryAndMetadata();
      showNotification('Traitement des outliers réussi');
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors du traitement des outliers');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const cleanText = useCallback(async (column, options = {}) => {
    setLoading(true);
    try {
      await apiClient.post('/api/cleaning/text', {
        column,
        strip: options.strip ?? true,
        casing: options.casing ?? 'lower',
        empty_to_nan: options.emptyToNan ?? true,
      }, { params: { session_id: sessionId } });

      await refreshHistoryAndMetadata();
      showNotification('Nettoyage textuel réussi');
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors du nettoyage textuel');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const removeDuplicates = useCallback(async (subset = null, keep = 'first') => {
    setLoading(true);
    try {
      await apiClient.post('/api/cleaning/duplicates', {
        subset,
        keep,
      }, { params: { session_id: sessionId } });
      
      await refreshHistoryAndMetadata();
      showNotification('Doublons supprimés');
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors de la suppression des doublons');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const dropColumns = useCallback(async (columns) => {
    setLoading(true);
    try {
      await apiClient.post('/api/cleaning/drop-columns', {
        columns,
      }, { params: { session_id: sessionId } });

      await refreshHistoryAndMetadata();
      showNotification('Colonnes supprimées');
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors de la suppression des colonnes');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const undoLastOperation = useCallback(async () => {
    setLoading(true);
    try {
      await apiClient.post('/api/cleaning/undo', null, {
        params: { session_id: sessionId },
      });
      
      await refreshHistoryAndMetadata();
      showNotification('Opération annulée');
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de l'annulation");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const resetDataset = useCallback(async () => {
    setLoading(true);
    try {
      await apiClient.post('/api/cleaning/reset', null, {
        params: { session_id: sessionId },
      });
      
      await refreshHistoryAndMetadata();
      showNotification('Dataset réinitialisé');
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors de la réinitialisation');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  // Feature Engineering / Transformations
  const extractDatetimeFeatures = useCallback(async (column, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/transforms/datetime', {
        column,
        extract_year: options.extractYear ?? true,
        extract_month: options.extractMonth ?? true,
        extract_day: options.extractDay ?? true,
        extract_dayofweek: options.extractDayOfWeek ?? true,
        extract_hour: options.extractHour ?? false,
        extract_is_weekend: options.extractIsWeekend ?? true,
        extract_quarter: options.extractQuarter ?? true,
        reference_date: options.referenceDate || null
      }, { params: { session_id: sessionId } });

      await refreshHistoryAndMetadata();
      showNotification(response.data.message || 'Caractéristiques temporelles extraites avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de l'extraction temporelle");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const createNumericInteraction = useCallback(async (colA, colB, operation, outputName = null) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/transforms/numeric-interaction', {
        col_a: colA,
        col_b: colB,
        operation,
        output_name: outputName || null
      }, { params: { session_id: sessionId } });

      await refreshHistoryAndMetadata();
      showNotification(response.data.message || 'Interaction numérique créée');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur interaction numérique");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const binNumericColumn = useCallback(async (column, nBins = 5, strategy = 'quantile', outputName = null) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/transforms/binning', {
        column,
        n_bins: nBins,
        strategy,
        output_name: outputName || null
      }, { params: { session_id: sessionId } });

      await refreshHistoryAndMetadata();
      showNotification(response.data.message || 'Colonne discrétisée avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur discrétisation");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const extractTextFeatures = useCallback(async (column, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/transforms/text-features', {
        column,
        extract_char_length: options.extractCharLength ?? true,
        extract_word_count: options.extractWordCount ?? true,
        vectorize_method: options.vectorizeMethod || null,
        max_features: options.maxFeatures || 50
      }, { params: { session_id: sessionId } });

      await refreshHistoryAndMetadata();
      showNotification(response.data.message || 'Caractéristiques textuelles extraites');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur extraction textuelle");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, refreshHistoryAndMetadata, showNotification]);

  const buildSupervisedPipeline = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/ml/supervised', {
        ...params,
      }, { params: { session_id: sessionId } });
      
      setMlResults(response.data);
      showNotification('Pipeline ML créé avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors de la création du pipeline');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const exportCleanedDataset = useCallback(async (filename = 'dataset_cleaned', formatType = 'csv') => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/export/cleaned', {
        filename,
        format_type: formatType,
      }, { 
        params: { session_id: sessionId },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${filename}.${formatType === 'excel' ? 'xlsx' : 'csv'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showNotification('Export du dataset nettoyé réussi');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de l'export");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const generateReport = useCallback(async (filename = 'rapport_preparation', formatType = 'html') => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/export/report', {
        filename,
        format_type: formatType,
      }, { 
        params: { session_id: sessionId },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const extension = (formatType === 'word' || formatType === 'docx') ? 'docx' : 
                       (formatType === 'excel' || formatType === 'xlsx') ? 'xlsx' : 
                       formatType === 'markdown' ? 'md' : 'html';
      link.setAttribute('download', `${filename}.${extension}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showNotification(`Rapport ${formatType.toUpperCase()} généré et téléchargé`);
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, 'Erreur lors de la génération du rapport');
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const exportMLSplits = useCallback(async (prefix = 'ml_data', formatType = 'csv', splitName = null) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/export/splits', {
        prefix,
        format_type: formatType,
        split_name: splitName
      }, { 
        params: { session_id: sessionId },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      if (splitName) {
        link.setAttribute('download', `${prefix}_${splitName}.${formatType === 'excel' ? 'xlsx' : 'csv'}`);
      } else if (formatType === 'excel') {
        link.setAttribute('download', `${prefix}_splits.xlsx`);
      } else {
        link.setAttribute('download', `${prefix}_splits.zip`);
      }
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showNotification(splitName ? `Split ${splitName} exporté` : 'Splits ML exportés avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de l'export des splits ML");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const exportPipeline = useCallback(async (filename = 'fitted_pipeline.joblib') => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/export/pipeline', {
        filename,
      }, { 
        params: { session_id: sessionId },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      showNotification('Pipeline joblib exportée avec succès');
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de l'export de la pipeline");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const generateInferenceScript = useCallback(async (pipelineJoblibName = 'fitted_pipeline.joblib', outputScriptName = 'run_inference.py') => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/export/inference-script', null, {
        params: {
          pipeline_joblib_name: pipelineJoblibName,
          output_script_name: outputScriptName,
          session_id: sessionId
        },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', outputScriptName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      showNotification("Script d'inférence généré avec succès");
      return response.data;
    } catch (err) {
      const errorMsg = await extractErrorMessage(err, "Erreur lors de la génération du script");
      setError(errorMsg);
      showNotification(errorMsg, 'error');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [sessionId, showNotification]);

  const value = {
    sessionId,
    metadata,
    analysisResults,
    cleaningHistory,
    mlResults,
    loading,
    error,
    notification,
    uploadDataset,
    getPreview,
    runAnalysis,
    selectTargetVariable,
    getCorrelationHeatmap,
    compareBeforeAfter,
    imputeMissing,
    handleOutliers,
    cleanText,
    removeDuplicates,
    dropColumns,
    undoLastOperation,
    resetDataset,
    refreshHistoryAndMetadata,
    extractDatetimeFeatures,
    createNumericInteraction,
    binNumericColumn,
    extractTextFeatures,
    exportCleanedDataset,
    generateReport,
    exportMLSplits,
    exportPipeline,
    generateInferenceScript,
    buildSupervisedPipeline,
  };

  return (
    <DataContext.Provider value={value}>
      {children}
      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all ${
          notification.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
        }`}>
          {notification.message}
        </div>
      )}
    </DataContext.Provider>
  );
};
