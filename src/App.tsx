import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar, NavTab } from './components/Navbar';
import { SummaryView } from './components/SummaryView';
import { RiskCalculator } from './components/RiskCalculator';
import { SqlExplorer } from './components/SqlExplorer';
import { DashboardView } from './components/dashboard/DashboardView';
import { AdminPanel } from './components/admin/AdminPanel';
import { AuthProvider } from './context/AuthContext';
import { REPO_META } from './data/repoData';
import { Github, ExternalLink } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors selection:bg-blue-500 selection:text-white">
          {/* Sticky Navigation Bar */}
          <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

          {/* Main Container */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
            {activeTab === 'dashboard' && <DashboardView />}

            {activeTab === 'admin' && <AdminPanel />}

            {activeTab === 'summary' && (
              <SummaryView 
                onOpenPredictor={() => setActiveTab('calculator')}
                onOpenSql={() => setActiveTab('sql')}
                onOpenDashboard={() => setActiveTab('dashboard')}
              />
            )}

            {activeTab === 'calculator' && <RiskCalculator />}

            {activeTab === 'sql' && <SqlExplorer />}
          </main>

          {/* Footer */}
          <footer className="mt-auto border-t border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 backdrop-blur-sm py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 dark:text-slate-400 gap-3">
              <div className="flex items-center space-x-1.5">
                <span>Healthcare Data Warehouse &amp; Analytics Platform for</span>
                <a
                  href={REPO_META.repoUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="font-semibold text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 underline"
                >
                  sripoojithag/healthcare_analytics
                </a>
              </div>

              <div className="flex items-center space-x-4">
                <a
                  href={REPO_META.liveDemoUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-blue-600 dark:hover:text-blue-400 flex items-center"
                >
                  Streamlit App <ExternalLink className="w-3 h-3 ml-1" />
                </a>
                <a
                  href={REPO_META.repoUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-slate-900 dark:hover:text-white flex items-center"
                >
                  <Github className="w-3.5 h-3.5 mr-1" /> GitHub
                </a>
              </div>
            </div>
          </footer>
        </div>
      </AuthProvider>
    </QueryClientProvider>
  );
}
