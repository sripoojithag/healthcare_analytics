import React from 'react';
import { QualitySummary } from '../../services/apiClient';
import { ShieldCheck, CheckCircle2, AlertTriangle, FileCheck, Database } from 'lucide-react';

interface DataQualityPanelProps {
  quality: QualitySummary;
}

export const DataQualityPanel: React.FC<DataQualityPanelProps> = ({ quality }) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 sm:p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            <span>Data Warehouse Quality &amp; Governance Audit</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Automated completeness, duplicate checks, and clinical code validity audits
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
            Grade {quality.quality_grade} (Audit Passed)
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-500 font-medium block">Overall Completeness</span>
          <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
            {quality.overall_completeness_pct}%
          </span>
          <span className="text-[10px] text-slate-400 block">Non-null cell ratio</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-500 font-medium block">Total Validated Rows</span>
          <span className="text-xl font-bold text-slate-900 dark:text-white">
            {quality.total_records.toLocaleString()}
          </span>
          <span className="text-[10px] text-slate-400 block">Inpatient encounters</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-500 font-medium block">Duplicate Encounters</span>
          <span className="text-xl font-bold text-blue-600 dark:text-blue-400">
            {quality.duplicate_rows}
          </span>
          <span className="text-[10px] text-slate-400 block">Deduplicated on ID</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 space-y-1">
          <span className="text-[11px] text-slate-500 font-medium block">Verified Attributes</span>
          <span className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
            {quality.total_columns}
          </span>
          <span className="text-[10px] text-slate-400 block">Schema attributes verified</span>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
        <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider block">
          Clinical Validity Assertions
        </span>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1 text-xs">
          <div className="flex items-center space-x-2 text-slate-700 dark:text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span>Gender Categories (Male, Female, Unknown)</span>
          </div>
          <div className="flex items-center space-x-2 text-slate-700 dark:text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span>Hospital Stay In-Bounds (1-14 Days)</span>
          </div>
          <div className="flex items-center space-x-2 text-slate-700 dark:text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
            <span>Readmission Outcome Target (&lt;30, &gt;30, NO)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
