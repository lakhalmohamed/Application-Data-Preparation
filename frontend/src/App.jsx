import React, { useState } from 'react';
import { DataProvider } from './context/DataContext';
import Sidebar from './components/Sidebar';
import ImportPage from './pages/ImportPage';
import EDAPage from './pages/EDAPage';
import AuditPage from './pages/AuditPage';
import CleaningPage from './pages/CleaningPage';
import TransformsPage from './pages/TransformsPage';
import MLConfigPage from './pages/MLConfigPage';
import ExportPage from './pages/ExportPage';
import ComparisonPage from './pages/ComparisonPage';

function App() {
  const [currentPage, setCurrentPage] = useState('import');

  const renderPage = () => {
    switch (currentPage) {
      case 'import':
        return <ImportPage />;
      case 'eda':
        return <EDAPage />;
      case 'audit':
        return <AuditPage />;
      case 'cleaning':
        return <CleaningPage />;
      case 'transforms':
        return <TransformsPage />;
      case 'ml':
        return <MLConfigPage />;
      case 'export':
        return <ExportPage />;
      case 'comparison':
        return <ComparisonPage />;
      default:
        return <ImportPage />;
    }
  };

  return (
    <DataProvider>
      <div className="flex min-h-screen bg-background">
        <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
        <main className="flex-1 overflow-auto">
          {renderPage()}
        </main>
      </div>
    </DataProvider>
  );
}

export default App;
