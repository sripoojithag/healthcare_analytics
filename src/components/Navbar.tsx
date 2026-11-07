import React, { useState } from 'react';
import { 
  ExternalLink, 
  Github, 
  Stethoscope, 
  Activity, 
  Sparkles, 
  BookOpen, 
  Calculator, 
  Database, 
  FileText, 
  LayoutDashboard,
  ShieldAlert,
  LogIn,
  LogOut,
  User,
  ShieldCheck
} from 'lucide-react';
import { REPO_META } from '../data/repoData';
import { useAuth } from '../context/AuthContext';
import { LoginModal } from './auth/LoginModal';

export type NavTab = 'dashboard' | 'admin' | 'summary' | 'calculator' | 'sql';

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-50 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Project Title */}
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
                <Stethoscope className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-900 dark:text-white text-base sm:text-lg tracking-tight">
                    Healthcare Analytics
                  </span>
                  <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
                    <Activity className="w-3 h-3 mr-1" /> Full Platform
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  github.com/{REPO_META.owner}/{REPO_META.name}
                </p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center space-x-1">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === 'dashboard'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </button>

              {/* Admin Panel Tab - Rendered ONLY if the server reports the current user is an admin */}
              {isAdmin && (
                <button
                  onClick={() => setActiveTab('admin')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                    activeTab === 'admin'
                      ? 'bg-purple-600 text-white shadow-sm'
                      : 'text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/40 hover:bg-purple-100'
                  }`}
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>Admin Panel</span>
                </button>
              )}

              <button
                onClick={() => setActiveTab('summary')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'summary'
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <BookOpen className="w-4 h-4" />
                <span>Overview</span>
              </button>

              <button
                onClick={() => setActiveTab('calculator')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'calculator'
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <Calculator className="w-4 h-4" />
                <span>Legacy</span>
              </button>

              <button
                onClick={() => setActiveTab('sql')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === 'sql'
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                <Database className="w-4 h-4" />
                <span>SQL</span>
              </button>
            </nav>

            {/* Action Links & Auth */}
            <div className="flex items-center space-x-2">
              {/* User Authentication Status */}
              {isAuthenticated && user ? (
                <div className="relative">
                  <button
                    onClick={() => setShowUserDropdown(!showUserDropdown)}
                    className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 transition-colors"
                  >
                    <span className={`w-2 h-2 rounded-full ${
                      user.role === 'admin' ? 'bg-purple-500' : user.role === 'analyst' ? 'bg-blue-500' : 'bg-emerald-500'
                    }`} />
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">{user.name.split(' ')[0]}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded uppercase ${
                      user.role === 'admin' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/60 dark:text-purple-300' : user.role === 'analyst' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-300' : 'bg-slate-200 text-slate-700'
                    }`}>
                      {user.role}
                    </span>
                  </button>

                  {showUserDropdown && (
                    <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 p-2 z-50 animate-fade-in">
                      <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800">
                        <div className="text-xs font-bold text-slate-900 dark:text-white truncate">{user.name}</div>
                        <div className="text-[11px] text-slate-500 truncate">{user.email}</div>
                      </div>

                      {isAdmin && (
                        <button
                          onClick={() => {
                            setActiveTab('admin');
                            setShowUserDropdown(false);
                          }}
                          className="w-full text-left px-3 py-2 text-xs font-semibold text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-950/40 rounded-lg flex items-center space-x-2 mt-1"
                        >
                          <ShieldAlert className="w-3.5 h-3.5" />
                          <span>Admin Control Center</span>
                        </button>
                      )}

                      <button
                        onClick={async () => {
                          await logout();
                          setShowUserDropdown(false);
                          if (activeTab === 'admin') setActiveTab('dashboard');
                        }}
                        className="w-full text-left px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg flex items-center space-x-2 mt-1"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-all"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Sign In</span>
                </button>
              )}

              <a
                href={REPO_META.liveDemoUrl}
                target="_blank"
                rel="noreferrer"
                className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-xs transition-all"
                title="Open Streamlit Live Demo"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Streamlit</span>
                <ExternalLink className="w-3 h-3 ml-0.5 opacity-80" />
              </a>

              <a
                href={REPO_META.repoUrl}
                target="_blank"
                rel="noreferrer"
                className="p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-lg transition-all"
                title="View on GitHub"
              >
                <Github className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Mobile Navigation bar */}
          <div className="flex md:hidden overflow-x-auto space-x-2 py-2 border-t border-slate-100 dark:border-slate-800 no-scrollbar">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-bold ${
                activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
              }`}
            >
              Dashboard
            </button>
            {isAdmin && (
              <button
                onClick={() => setActiveTab('admin')}
                className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-bold ${
                  activeTab === 'admin' ? 'bg-purple-600 text-white' : 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300'
                }`}
              >
                Admin Panel
              </button>
            )}
            <button
              onClick={() => setActiveTab('summary')}
              className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-medium ${
                activeTab === 'summary' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('calculator')}
              className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-medium ${
                activeTab === 'calculator' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
              }`}
            >
              Legacy
            </button>
            <button
              onClick={() => setActiveTab('sql')}
              className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-medium ${
                activeTab === 'sql' ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
              }`}
            >
              SQL
            </button>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </>
  );
};
