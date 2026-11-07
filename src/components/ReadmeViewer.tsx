import React, { useState } from 'react';
import { FileText, Copy, Check, Folder, File, ExternalLink, Github, Code, Eye } from 'lucide-react';
import { REPO_META, REPO_STRUCTURE } from '../data/repoData';

export const ReadmeViewer: React.FC = () => {
  const [viewMode, setViewMode] = useState<'formatted' | 'raw'>('formatted');
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(REPO_META.rawReadme);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800 mb-2">
            <Github className="w-3.5 h-3.5" />
            <span>GitHub Repository Viewer</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">
            Repository README.md &amp; File Structure
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Directly synced from <a href={REPO_META.repoUrl} target="_blank" rel="noreferrer" className="text-blue-600 dark:text-blue-400 underline font-mono">github.com/{REPO_META.owner}/{REPO_META.name}</a> (branch: <code className="font-mono">main</code>).
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setViewMode('formatted')}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === 'formatted'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Rendered</span>
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === 'raw'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>Raw Markdown</span>
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="inline-flex items-center space-x-1 px-3 py-2 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-all"
            title="Copy Raw README.md"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Repository File Tree */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center">
                <Folder className="w-3.5 h-3.5 mr-1.5 text-amber-500" />
                Repository Tree
              </h3>
              <a
                href={REPO_META.repoUrl}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] text-blue-600 dark:text-blue-400 hover:underline flex items-center"
              >
                GitHub <ExternalLink className="w-3 h-3 ml-0.5" />
              </a>
            </div>

            <div className="space-y-2">
              {REPO_STRUCTURE.map((item, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-800/40 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between font-mono font-medium text-slate-800 dark:text-slate-200">
                    <span className="flex items-center">
                      {item.type === 'dir' ? (
                        <Folder className="w-3.5 h-3.5 mr-1.5 text-amber-500 flex-shrink-0" />
                      ) : (
                        <File className="w-3.5 h-3.5 mr-1.5 text-blue-500 flex-shrink-0" />
                      )}
                      {item.path}
                    </span>
                    <span className="text-[10px] text-slate-400 font-sans">{item.size}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* README Content Viewer */}
        <div className="lg:col-span-8">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
            {viewMode === 'raw' ? (
              <div className="bg-slate-950 rounded-xl p-4 font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre leading-relaxed border border-slate-800">
                {REPO_META.rawReadme}
              </div>
            ) : (
              <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 space-y-6">
                <div className="border-b border-slate-200 dark:border-slate-800 pb-4">
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Healthcare Readmission Risk Prediction
                  </h1>
                </div>

                <section className="space-y-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
                    Project Overview
                  </h2>
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    This project analyzes hospital patient data to predict the risk of patient readmission. The goal is to help hospitals identify high-risk patients early and reduce readmission rates.
                  </p>
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">This project includes:</p>
                  <ul className="list-disc pl-5 text-sm text-slate-600 dark:text-slate-300 space-y-1">
                    <li>Data Cleaning &amp; Analysis (Python, Pandas)</li>
                    <li>Machine Learning Model (Random Forest)</li>
                    <li>Interactive Dashboard (Power BI)</li>
                    <li>Risk Prediction Web App (Streamlit)</li>
                  </ul>
                </section>

                <hr className="border-slate-200 dark:border-slate-800" />

                <section className="space-y-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
                    Project Architecture
                  </h2>
                  <div className="p-3 bg-slate-100 dark:bg-slate-800/80 rounded-lg font-mono text-xs text-slate-800 dark:text-slate-200 font-semibold overflow-x-auto">
                    Raw Data → Data Cleaning → Feature Engineering → Machine Learning Model → Dashboard → Web App
                  </div>
                </section>

                <hr className="border-slate-200 dark:border-slate-800" />

                <section className="space-y-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
                    Tech Stack
                  </h2>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {['Python', 'Pandas', 'Scikit-Learn', 'Streamlit', 'Power BI', 'SQL'].map((t) => (
                      <span key={t} className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                        {t}
                      </span>
                    ))}
                  </div>
                </section>

                <hr className="border-slate-200 dark:border-slate-800" />

                <section className="space-y-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
                    Key Insights
                  </h2>
                  <ul className="list-disc pl-5 text-sm text-slate-600 dark:text-slate-300 space-y-1.5">
                    <li>Patients with longer hospital stays have higher readmission risk</li>
                    <li>Higher number of lab procedures correlates with readmission</li>
                    <li>Older age groups show higher risk</li>
                    <li>Medication count influences readmission probability</li>
                    <li>Certain medical specialties have higher readmission cases</li>
                  </ul>
                </section>

                <hr className="border-slate-200 dark:border-slate-800" />

                <section className="space-y-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
                    Machine Learning Model
                  </h2>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    <strong>Algorithm used:</strong> Random Forest Classifier<br />
                    <strong>Model Accuracy:</strong> <span className="text-emerald-600 dark:text-emerald-400 font-bold">88%</span>
                  </p>
                </section>

                <hr className="border-slate-200 dark:border-slate-800" />

                <section className="space-y-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
                    Risk Categories
                  </h2>
                  <div className="grid grid-cols-3 gap-2 py-1">
                    <div className="p-2 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-center text-xs font-bold border border-emerald-200 dark:border-emerald-800">
                      Low Risk
                    </div>
                    <div className="p-2 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 text-center text-xs font-bold border border-amber-200 dark:border-amber-800">
                      Medium Risk
                    </div>
                    <div className="p-2 rounded bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-center text-xs font-bold border border-rose-200 dark:border-rose-800">
                      High Risk
                    </div>
                  </div>
                  <p className="text-xs text-slate-500">
                    Risk score is calculated using: Time in hospital, Number of lab procedures, Number of medications
                  </p>
                </section>

                <hr className="border-slate-200 dark:border-slate-800" />

                <section className="space-y-2">
                  <h2 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
                    Live Demo Link
                  </h2>
                  <p className="text-sm">
                    <a
                      href={REPO_META.liveDemoUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline font-mono inline-flex items-center"
                    >
                      {REPO_META.liveDemoUrl}
                      <ExternalLink className="w-3.5 h-3.5 ml-1" />
                    </a>
                  </p>
                </section>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
