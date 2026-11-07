import React, { useState } from 'react';
import { Database, Copy, Check, Terminal, Play, Table, Layers, ArrowUpRight } from 'lucide-react';
import { REPO_SQL_QUERIES, SQLQuery } from '../data/repoData';

export const SqlExplorer: React.FC = () => {
  const [selectedQueryId, setSelectedQueryId] = useState<string>(REPO_SQL_QUERIES[0].id);
  const [copied, setCopied] = useState<boolean>(false);

  const selectedQuery = REPO_SQL_QUERIES.find((q) => q.id === selectedQueryId) || REPO_SQL_QUERIES[0];

  const handleCopy = (sql: string) => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 mb-2">
            <Database className="w-3.5 h-3.5" />
            <span>sql/analytics_queries.sql</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">
            Healthcare SQL Analytics Suite
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            7 structured analytical queries developed in the repository to extract patient cohort demographics, hospital stay distributions, medication frequencies, and 30-day readmission rankings.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            7 Queries Available
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Queries List Sidebar */}
        <div className="lg:col-span-4 space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block px-1">
            Query Catalog
          </span>
          <div className="space-y-1.5">
            {REPO_SQL_QUERIES.map((query) => (
              <button
                key={query.id}
                onClick={() => setSelectedQueryId(query.id)}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  selectedQueryId === query.id
                    ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-700 shadow-sm'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-bold ${
                    selectedQueryId === query.id ? 'text-blue-700 dark:text-blue-300' : 'text-slate-900 dark:text-white'
                  }`}>
                    {query.title}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded capitalize ${
                    query.category === 'risk' 
                      ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300' 
                      : query.category === 'demographics'
                      ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300'
                      : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'
                  }`}>
                    {query.category}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
                  {query.purpose}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Query Details */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-2">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {selectedQuery.title}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  <strong className="text-slate-700 dark:text-slate-300">Stated Purpose:</strong> {selectedQuery.purpose}
                </p>
              </div>

              <button
                onClick={() => handleCopy(selectedQuery.sql)}
                className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-all self-start sm:self-auto"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy SQL'}</span>
              </button>
            </div>

            {/* SQL Code Block */}
            <div className="relative rounded-xl overflow-hidden bg-slate-950 border border-slate-800 p-4 font-mono text-xs text-slate-200 leading-relaxed shadow-inner">
              <div className="flex items-center space-x-1.5 text-slate-500 text-[11px] pb-3 border-b border-slate-800/80 mb-3">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span>PostgreSQL / MySQL Compatible</span>
              </div>
              <pre className="overflow-x-auto text-emerald-300">
                <code>{selectedQuery.sql}</code>
              </pre>
            </div>

            {/* Simulated Query Results Preview */}
            {selectedQuery.mockResults && (
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center">
                    <Table className="w-3.5 h-3.5 mr-1.5 text-blue-500" />
                    Dataset Sample Output
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {selectedQuery.mockResults.rows.length} rows previewed
                  </span>
                </div>

                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-800/60 font-semibold text-slate-700 dark:text-slate-300">
                      <tr>
                        {selectedQuery.mockResults.columns.map((col, idx) => (
                          <th key={idx} className="px-3.5 py-2.5 text-left font-mono">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50 bg-white dark:bg-slate-900 font-mono text-slate-600 dark:text-slate-400">
                      {selectedQuery.mockResults.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                          {row.map((cell, cIdx) => (
                            <td key={cIdx} className="px-3.5 py-2 whitespace-nowrap">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
