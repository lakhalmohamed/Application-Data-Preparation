import React, { useState, useEffect } from 'react';
import { useData } from '../context/DataContext';
import Plot from 'react-plotly.js';
import { BarChart3, Grid } from 'lucide-react';

const EDAPage = () => {
  const { analysisResults, metadata, getCorrelationHeatmap } = useData();
  const [selectedColumn, setSelectedColumn] = useState('');
  const [chartType, setChartType] = useState('histogram');
  const [columnProfile, setColumnProfile] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [viewMode, setViewMode] = useState('column'); // 'column' or 'heatmap'

  useEffect(() => {
    if (analysisResults && analysisResults.profiles) {
      const columns = Object.keys(analysisResults.profiles);
      if (columns.length > 0 && !selectedColumn) {
        setSelectedColumn(columns[0]);
      }
    }
  }, [analysisResults]);

  useEffect(() => {
    if (selectedColumn && analysisResults?.profiles?.[selectedColumn]) {
      setColumnProfile(analysisResults.profiles[selectedColumn]);
    }
  }, [selectedColumn, analysisResults]);

  useEffect(() => {
    if (viewMode === 'heatmap' && analysisResults && !heatmapData) {
      fetchHeatmapData();
    }
  }, [viewMode, analysisResults]);

  const fetchHeatmapData = async () => {
    try {
      const data = await getCorrelationHeatmap();
      setHeatmapData(data);
    } catch (err) {
      console.error('Failed to fetch heatmap data:', err);
    }
  };

  if (!analysisResults) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Aucune analyse disponible
          </h3>
          <p className="text-yellow-700">
            Lancez l'analyse depuis la page Import pour voir les résultats.
          </p>
        </div>
      </div>
    );
  }

  const columns = Object.keys(analysisResults.profiles);
  const profile = columnProfile;

  const generateChartData = () => {
    if (!profile) return null;

    const stats = profile.stats;
    const isNumeric = profile.detected_type?.toLowerCase().includes('num') || 
                      ['int', 'float'].some(t => (profile.pandas_dtype || '').toLowerCase().includes(t));
    
    if (chartType === 'histogram' && isNumeric) {
      return {
        data: [{
          x: stats.top_values ? Object.keys(stats.top_values) : [],
          y: stats.top_values ? Object.values(stats.top_values) : [],
          type: 'bar',
          marker: { color: '#2563eb' },
        }],
        layout: {
          title: `Distribution de ${selectedColumn}`,
          xaxis: { title: selectedColumn },
          yaxis: { title: 'Effectif' },
        },
      };
    }

    if (chartType === 'bar' && stats.top_values) {
      return {
        data: [{
          x: Object.values(stats.top_values),
          y: Object.keys(stats.top_values),
          type: 'bar',
          orientation: 'h',
          marker: { color: '#6366f1' },
        }],
        layout: {
          title: `Fréquences de ${selectedColumn}`,
          xaxis: { title: 'Effectif' },
          yaxis: { title: selectedColumn },
        },
      };
    }

    if (chartType === 'boxplot' && isNumeric) {
      return {
        data: [{
          y: [stats.min, stats.q25, stats.median, stats.q75, stats.max],
          type: 'box',
          marker: { color: '#93c5fd' },
        }],
        layout: {
          title: `Boxplot de ${selectedColumn}`,
        },
      };
    }

    return null;
  };

  const chartData = generateChartData();

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Analyse Exploratoire</h1>
        <p className="text-gray-600">Profilage des variables et visualisations</p>
      </div>

      {/* View Mode Toggle */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setViewMode('column')}
          className={`px-4 py-2 rounded-lg font-medium ${
            viewMode === 'column'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <BarChart3 className="w-4 h-4 inline mr-2" />
          Analyse par Variable
        </button>
        <button
          onClick={() => setViewMode('heatmap')}
          className={`px-4 py-2 rounded-lg font-medium ${
            viewMode === 'heatmap'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Grid className="w-4 h-4 inline mr-2" />
          Matrice de Corrélation
        </button>
      </div>

      {viewMode === 'column' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Panel: Column Selection and Profile */}
        <div className="bg-card rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Sélectionner une variable</h2>
          <select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-6"
          >
            {columns.map((col) => (
              <option key={col} value={col}>
                {col}
              </option>
            ))}
          </select>

          {profile && (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Type détecté</h3>
                <p className="text-gray-700">{profile.detected_type}</p>
                <p className="text-sm text-gray-500">Confiance: {profile.confidence} ({Math.round(profile.confidence_score * 100)}%)</p>
              </div>

              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Statistiques</h3>
                <div className="space-y-1 text-sm">
                  <p>Observations: {profile.stats.total_count} ({profile.stats.non_null_count} renseignées)</p>
                  <p>Manquantes: {profile.stats.missing_count} ({profile.stats.missing_pct}%)</p>
                  <p>Distinctes: {profile.stats.unique_count} ({profile.stats.unique_pct}%)</p>
                  {profile.stats.mean && (
                    <>
                      <p>Moyenne: {profile.stats.mean?.toFixed(4)}</p>
                      <p>Médiane: {profile.stats.median?.toFixed(4)}</p>
                      <p>Écart-type: {profile.stats.std?.toFixed(4)}</p>
                      <p>Min/Max: {profile.stats.min?.toFixed(4)} / {profile.stats.max?.toFixed(4)}</p>
                    </>
                  )}
                </div>
              </div>

              {profile.issues && profile.issues.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Problèmes identifiés</h3>
                  <div className="space-y-2">
                    {profile.issues.map((issue, idx) => (
                      <div key={idx} className="p-2 bg-red-50 rounded text-sm">
                        <p className="font-medium text-red-800">[{issue.severity}] {issue.issue}</p>
                        <p className="text-red-600">{issue.details}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {profile.recommendations && profile.recommendations.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Recommandations</h3>
                  <div className="space-y-2">
                    {profile.recommendations.map((rec, idx) => (
                      <div key={idx} className="p-2 bg-blue-50 rounded text-sm">
                        <p className="font-medium text-blue-800">{rec.action}</p>
                        <p className="text-blue-600">{rec.justification}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Panel: Charts */}
        <div className="bg-card rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Visualisation</h2>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="histogram">Histogramme</option>
              <option value="bar">Bar Chart</option>
              <option value="boxplot">Boxplot</option>
            </select>
          </div>

          {chartData ? (
            <Plot
              data={chartData.data}
              layout={chartData.layout}
              style={{ width: '100%', height: '400px' }}
              useResizeHandler
            />
          ) : (
            <div className="h-96 flex items-center justify-center text-gray-500">
              Sélectionnez un type de graphique compatible
            </div>
          )}
        </div>
      </div>
      ) : (
        /* Heatmap View */
        <div className="bg-card rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Matrice de Corrélation</h2>
          {heatmapData && heatmapData.z && heatmapData.z.length > 0 ? (
            <Plot
              data={[
                {
                  z: heatmapData.z,
                  x: heatmapData.x,
                  y: heatmapData.y,
                  type: 'heatmap',
                  colorscale: 'RdBu',
                  reversescale: true,
                  colorbar: {
                    title: 'Corrélation'
                  }
                }
              ]}
              layout={{
                title: 'Matrice de Corrélation des Variables Numériques',
                xaxis: { title: 'Variables' },
                yaxis: { title: 'Variables' },
                width: 800,
                height: 600
              }}
              style={{ width: '100%', height: '600px' }}
              useResizeHandler
            />
          ) : (
            <div className="h-96 flex items-center justify-center text-gray-500">
              {heatmapData?.message || 'Chargement de la matrice de corrélation...'}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EDAPage;
