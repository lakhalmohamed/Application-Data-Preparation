import React from 'react';
import { useData } from '../context/DataContext';
import { Search, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const AuditPage = () => {
  const { analysisResults } = useData();

  if (!analysisResults) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <Search className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Aucune analyse disponible
          </h3>
          <p className="text-yellow-700">
            Lancez l'analyse depuis la page Import pour voir l'audit de qualité.
          </p>
        </div>
      </div>
    );
  }

  const issues = analysisResults.global_issues || [];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'Critique':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'Élevée':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'Moyenne':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Faible':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'Critique':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'Élevée':
        return <AlertTriangle className="w-5 h-5 text-orange-600" />;
      case 'Moyenne':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'Faible':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Audit de Qualité</h1>
        <p className="text-gray-600">Problèmes détectés et recommandations</p>
      </div>

      <div className="bg-card rounded-lg border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">
            {issues.length} problème(s) détecté(s)
          </h2>
        </div>

        {issues.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
            <p>Aucun problème de qualité détecté. Excellent !</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Variable
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Problème
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Gravité
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Impact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Action Recommandée
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Justification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    État
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {issues.map((issue, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {issue.variable}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {issue.issue}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(issue.severity)}`}>
                        {getSeverityIcon(issue.severity)}
                        {issue.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {issue.affected_count} ({issue.affected_pct}%)
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {issue.action}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs">
                      {issue.justification}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
                        issue.status === 'Corrigé' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {issue.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditPage;
