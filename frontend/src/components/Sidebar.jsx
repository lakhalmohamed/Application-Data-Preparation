import React from 'react';
import { 
  Home, BarChart3, Search, Sparkles, Settings, 
  Cpu, Download, Zap, ArrowLeftRight 
} from 'lucide-react';

const Sidebar = ({ currentPage, setCurrentPage }) => {
  const navItems = [
    { id: 'import', label: 'Accueil & Import', icon: Home },
    { id: 'eda', label: 'Analyse Exploratoire', icon: BarChart3 },
    { id: 'audit', label: 'Audit de Qualité', icon: Search },
    { id: 'cleaning', label: 'Nettoyage', icon: Sparkles },
    { id: 'transforms', label: 'Transformations', icon: Settings },
    { id: 'ml', label: 'Configuration ML', icon: Cpu },
    { id: 'comparison', label: 'Comparaison Avant/Après', icon: ArrowLeftRight },
    { id: 'export', label: 'Résultats & Export', icon: Download },
  ];

  return (
    <div className="w-64 bg-sidebar min-h-screen flex flex-col">
      <div className="p-6 border-b border-sidebar-hover">
        <div className="flex items-center gap-3">
          <Zap className="w-8 h-8 text-primary" />
          <div>
            <h1 className="text-white font-bold text-lg">AutoDataPrep</h1>
            <p className="text-gray-400 text-xs">ML Data Prep Studio</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => setCurrentPage(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-sidebar-active text-white'
                      : 'text-gray-300 hover:bg-sidebar-hover hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-sidebar-hover">
        <p className="text-gray-500 text-xs text-center">
          © 2024 AutoDataPrep
        </p>
      </div>
    </div>
  );
};

export default Sidebar;
