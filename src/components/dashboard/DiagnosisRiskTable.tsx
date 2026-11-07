import React from 'react';
import { DiagnosisMetric } from '../../services/apiClient';
import { Stethoscope, ShieldAlert } from 'lucide-react';

interface DiagnosisRiskTableProps {
  data: DiagnosisMetric[];
}

export const DiagnosisRiskTable: React.FC<DiagnosisRiskTableProps> = ({ data }) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 sm:p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
            <Stethoscope className="w-4 h-4 text-rose-500" />
            <span>Disease Category Risk Prioritization</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Ranked by 30-day readmission risk using SQL window ranking functions (RANK() OVER)
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
          Clinical Diagnostics
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/60 font-semibold text-slate-700 dark:text-slate-300">
            <tr>
              <th className="px-3 py-2.5 text-left">Risk Rank</th>
              <th className="px-3 py-2.5 text-left">Clinical Diagnosis Chapter</th>
              <th className="px-3 py-2.5 text-right">Encounters</th>
              <th className="px-3 py-2.5 text-right">&lt;30d Readmissions</th>
              <th className="px-3 py-2.5 text-right">Readmission Rate</th>
              <th className="px-3 py-2.5 text-right">Avg Stay</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400">
            {data.map((d) => (
              <tr key={d.diagnosis_category} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                <td className="px-3 py-2.5 whitespace-nowrap">
                  <span className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-[11px] font-bold ${
                    d.risk_rank === 1 ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300' :
                    d.risk_rank === 2 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300' :
                    'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                  }`}>
                    {d.risk_rank}
                  </span>
                </td>
                <td className="px-3 py-2.5 font-medium text-slate-900 dark:text-slate-200 whitespace-nowrap">
                  {d.diagnosis_category}
                </td>
                <td className="px-3 py-2.5 text-right font-mono">
                  {d.encounters.toLocaleString()}
                </td>
                <td className="px-3 py-2.5 text-right font-mono text-rose-600 dark:text-rose-400 font-semibold">
                  {d.readmissions_under_30.toLocaleString()}
                </td>
                <td className="px-3 py-2.5 text-right font-mono font-bold text-slate-900 dark:text-white">
                  {d.readmission_rate_pct.toFixed(2)}%
                </td>
                <td className="px-3 py-2.5 text-right font-mono">
                  {d.avg_length_of_stay.toFixed(1)} d
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
