import React from 'react';
import { 
  ArrowRight, 
  BrainCircuit, 
  CheckCircle2, 
  Clock, 
  Activity, 
  Users, 
  Pill, 
  Stethoscope, 
  Database, 
  LineChart, 
  Layers, 
  ExternalLink, 
  Sparkles, 
  ShieldAlert, 
  ChevronRight,
  TrendingUp,
  FileCode2,
  Workflow
} from 'lucide-react';
import { REPO_META } from '../data/repoData';

interface SummaryViewProps {
  onOpenPredictor: () => void;
  onOpenSql: () => void;
  onOpenDashboard?: () => void;
}

export const SummaryView: React.FC<SummaryViewProps> = ({ onOpenPredictor, onOpenSql, onOpenDashboard }) => {
  const getInsightIcon = (iconName: string) => {
    switch (iconName) {
      case 'Clock': return <Clock className="w-5 h-5 text-amber-500" />;
      case 'Activity': return <Activity className="w-5 h-5 text-emerald-500" />;
      case 'Users': return <Users className="w-5 h-5 text-indigo-500" />;
      case 'Pill': return <Pill className="w-5 h-5 text-purple-500" />;
      case 'Stethoscope': return <Stethoscope className="w-5 h-5 text-rose-500" />;
      default: return <Activity className="w-5 h-5 text-blue-500" />;
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white p-6 sm:p-8 shadow-xl border border-blue-900/40">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-4xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Healthcare Data Warehouse &amp; Analytics Platform (Phases 1-7)</span>
          </div>
          
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Healthcare Readmission Risk Prediction &amp; Analytics
          </h1>
          
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-3xl">
            A complete end-to-end healthcare intelligence system by <span className="text-white font-medium">sripoojithag</span> upgraded with an Azure-ready Star Schema data warehouse, clean ETL pipelines, leak-free Random Forest inference, FastAPI REST services, and role-based security.
          </p>

          {/* Quick Metrics Bar */}
          <div className="pt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <span className="text-xs text-slate-400 block font-medium">Warehouse Star Schema</span>
              <span className="text-base sm:text-lg font-bold text-white flex items-center mt-0.5">
                <Database className="w-4 h-4 mr-1 text-cyan-400" /> 1 Fact + 4 Dims
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <span className="text-xs text-slate-400 block font-medium">ML Pipeline (Leak-free)</span>
              <span className="text-base sm:text-lg font-bold text-emerald-400 flex items-center mt-0.5">
                <TrendingUp className="w-4 h-4 mr-1" /> ROC-AUC 0.66
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <span className="text-xs text-slate-400 block font-medium">Security &amp; RBAC</span>
              <span className="text-base sm:text-lg font-bold text-purple-300 flex items-center mt-0.5">
                <ShieldAlert className="w-4 h-4 mr-1 text-purple-400" /> 3 Roles + Audit
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <span className="text-xs text-slate-400 block font-medium">Backend &amp; Delivery</span>
              <span className="text-base sm:text-lg font-bold text-blue-300 flex items-center mt-0.5">
                <LineChart className="w-4 h-4 mr-1 text-blue-400" /> FastAPI + React
              </span>
            </div>
          </div>

          {/* Call to action buttons */}
          <div className="pt-2 flex flex-wrap gap-3">
            {onOpenDashboard && (
              <button
                onClick={onOpenDashboard}
                className="px-4 py-2 text-xs sm:text-sm font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30 inline-flex items-center space-x-1.5 transition-all"
              >
                <span>Launch Analytics Platform</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={onOpenPredictor}
              className="px-4 py-2 text-xs sm:text-sm font-medium rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 inline-flex items-center space-x-1.5 transition-all"
            >
              <span>Legacy Predictor</span>
            </button>
            <button
              onClick={onOpenSql}
              className="px-4 py-2 text-xs sm:text-sm font-medium rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 inline-flex items-center space-x-1.5 transition-all"
            >
              <Database className="w-4 h-4" />
              <span>Explore 7 SQL Queries</span>
            </button>
            <a
              href={REPO_META.liveDemoUrl}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 text-xs sm:text-sm font-medium rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-200 border border-rose-500/40 inline-flex items-center space-x-1.5 transition-all"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Visit Live Streamlit App</span>
            </a>
          </div>
        </div>
      </div>

      {/* Structured Sections Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Components */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <Workflow className="w-5 h-5 text-blue-600" />
                <span>Project Pipeline Architecture</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                The six-stage data lifecycle from patient ingestion to clinician-facing applications
              </p>
            </div>
            <span className="text-xs font-mono px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded">
              Raw Data → Web App
            </span>
          </div>

          <div className="space-y-3">
            {REPO_META.architectureSteps.map((step) => (
              <div 
                key={step.step}
                className="group flex items-start space-x-3.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:bg-blue-50/50 dark:hover:bg-blue-900/20 border border-slate-100 dark:border-slate-700/60 transition-all"
              >
                <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                  {step.step}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {step.name}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack Breakdown */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              <span>Technology Stack</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Tools and libraries utilized across the repo
            </p>
          </div>

          <div className="space-y-2.5">
            {REPO_META.techStack.map((tech) => (
              <div
                key={tech.name}
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-slate-800/40 transition-all"
              >
                <span className="font-semibold text-sm text-slate-800 dark:text-slate-200">
                  {tech.name}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${tech.color}`}>
                  {tech.category}
                </span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
            <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-300 space-y-1">
              <p className="font-semibold flex items-center">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-blue-600" />
                Dual Deployment Strategy
              </p>
              <p className="text-slate-600 dark:text-slate-400">
                • <strong>Power BI</strong> for executive and clinical leadership analytics dashboards.
                <br />
                • <strong>Streamlit</strong> for bedside / intake real-time patient risk scoring.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Insights Grid */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 dark:border-slate-800 pb-4 gap-2">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Activity className="w-5 h-5 text-emerald-600" />
              <span>Key Clinical & Analytical Insights</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Core statistical findings discovered through exploratory data analysis and modeling
            </p>
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            5 Critical Correlation Findings
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {REPO_META.keyInsights.map((insight, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-300 dark:hover:border-blue-700 bg-gradient-to-b from-white to-slate-50/50 dark:from-slate-900 dark:to-slate-800/50 transition-all hover:shadow-md space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800">
                  {getInsightIcon(insight.icon)}
                </div>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                  {insight.badge}
                </span>
              </div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                {insight.title}
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                {insight.detail}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* SQL & Streamlit Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SQL Queries Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <button
              onClick={onOpenSql}
              className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center"
            >
              View queries <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
            </button>
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              7 Dedicated SQL Analytics Queries
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
              Explores overall population counts, 30-day readmissions stratified by age cohorts, duration of inpatient stay distributions, metformin prescriptions, and window ranking functions.
            </p>
          </div>
          <div className="pt-2 flex flex-wrap gap-1.5">
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">COUNT(*)</span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">SUM(readmitted = '&lt;30')</span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">RANK() OVER(...)</span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">GROUP BY time_in_hospital</span>
          </div>
        </div>

        {/* Machine Learning & Streamlit Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 border border-rose-200 dark:border-rose-800 flex items-center justify-center">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <button
              onClick={onOpenPredictor}
              className="text-xs font-semibold text-rose-600 dark:text-rose-400 hover:underline flex items-center"
            >
              Try Simulator <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
            </button>
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Random Forest Risk Scoring Engine
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
              Trained on patient records with an impressive <strong>88% accuracy</strong>. Evaluates days in hospital (1-14), lab test volume (1-100), and medication count (1-50) into Low, Medium, and High risk classifications.
            </p>
          </div>
          <div className="pt-2 flex flex-wrap gap-1.5">
            <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 font-medium">Low: Score &le; 40</span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300 font-medium">Medium: 41 - 80</span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300 font-medium">High: &gt; 80</span>
          </div>
        </div>
      </div>

      {/* Future Improvements & Roadmap */}
      <div className="bg-slate-50 dark:bg-slate-900/60 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 space-y-4">
        <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-blue-500" />
          <span>Documented Future Improvements</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {REPO_META.futureRoadmap.map((item, index) => (
            <div
              key={index}
              className="flex items-start space-x-2.5 p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60"
            >
              <div className="mt-0.5 w-4 h-4 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300 flex items-center justify-center text-[10px] font-bold">
                {index + 1}
              </div>
              <span className="text-xs text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
                {item}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
