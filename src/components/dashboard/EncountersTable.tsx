import React, { useState } from 'react';
import { Lock, ShieldAlert, Eye, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

interface EncountersTableProps {
  currentRole: string;
}

export const EncountersTable: React.FC<EncountersTableProps> = ({ currentRole }) => {
  const [filter30d, setFilter30d] = useState<string>("all");
  const [page, setPage] = useState<number>(1);

  // If role is viewer, RBAC restricts encounter-level records
  if (currentRole === "viewer") {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 border border-amber-200 dark:border-amber-800 flex items-center justify-center mx-auto">
          <Lock className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Encounter-Level Data Restricted (Role: Viewer)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
            Per healthcare governance and Role-Based Access Control policies, individual encounter records with clinical diagnoses and medication regimens are restricted to <strong>Analyst</strong> and <strong>Admin</strong> roles.
          </p>
        </div>
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Switch role to Analyst or Admin above to unlock</span>
        </div>
      </div>
    );
  }

  // Sample masked data for Analyst/Admin review
  const encounters = [
    { id: "ENC10482", masked_patient: "PT-***2157", gender: "Female", age: "[70-80)", diag: "Circulatory (414)", stay: 4, labs: 45, meds: 16, insulin: "Up", readmit_30d: 1 },
    { id: "ENC10483", masked_patient: "PT-***9430", gender: "Male", age: "[60-70)", diag: "Diabetes (250)", stay: 3, labs: 38, meds: 12, insulin: "Steady", readmit_30d: 0 },
    { id: "ENC10484", masked_patient: "PT-***5512", gender: "Female", age: "[80-90)", diag: "Respiratory (486)", stay: 8, labs: 62, meds: 24, insulin: "Steady", readmit_30d: 1 },
    { id: "ENC10485", masked_patient: "PT-***1104", gender: "Male", age: "[50-60)", diag: "Digestive (540)", stay: 2, labs: 28, meds: 9, insulin: "No", readmit_30d: 0 },
    { id: "ENC10486", masked_patient: "PT-***7891", gender: "Female", age: "[70-80)", diag: "Circulatory (428)", stay: 6, labs: 54, meds: 21, insulin: "Down", readmit_30d: 1 },
    { id: "ENC10487", masked_patient: "PT-***4320", gender: "Male", age: "[40-50)", diag: "Injury (820)", stay: 1, labs: 15, meds: 6, insulin: "No", readmit_30d: 0 },
  ];

  const filtered = filter30d === "all" ? encounters : encounters.filter(e => filter30d === "yes" ? e.readmit_30d === 1 : e.readmit_30d === 0);

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 sm:p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
            <Eye className="w-4 h-4 text-blue-500" />
            <span>De-Identified Inpatient Encounters</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            HIPAA-aligned masked identifiers (<code className="font-mono text-blue-600">PT-***[suffix]</code>) with clinical encounter metrics
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={filter30d}
            onChange={(e) => setFilter30d(e.target.value)}
            className="text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
          >
            <option value="all">All Encounters</option>
            <option value="yes">Readmitted &lt; 30d Only</option>
            <option value="no">No 30d Readmission</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/60 font-semibold text-slate-700 dark:text-slate-300">
            <tr>
              <th className="px-3 py-2 text-left">Encounter ID</th>
              <th className="px-3 py-2 text-left">Masked Patient ID</th>
              <th className="px-3 py-2 text-left">Demographics</th>
              <th className="px-3 py-2 text-left">Primary Diagnosis</th>
              <th className="px-3 py-2 text-center">Stay (Days)</th>
              <th className="px-3 py-2 text-center">Labs</th>
              <th className="px-3 py-2 text-center">Meds</th>
              <th className="px-3 py-2 text-center">Insulin</th>
              <th className="px-3 py-2 text-right">30d Readmission</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 font-mono">
            {filtered.map((e) => (
              <tr key={e.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                <td className="px-3 py-2.5 font-bold text-slate-900 dark:text-white">{e.id}</td>
                <td className="px-3 py-2.5 text-blue-600 dark:text-blue-400 font-semibold">{e.masked_patient}</td>
                <td className="px-3 py-2.5 font-sans">{e.gender}, {e.age}</td>
                <td className="px-3 py-2.5 font-sans">{e.diag}</td>
                <td className="px-3 py-2.5 text-center">{e.stay}</td>
                <td className="px-3 py-2.5 text-center">{e.labs}</td>
                <td className="px-3 py-2.5 text-center">{e.meds}</td>
                <td className="px-3 py-2.5 text-center font-sans">{e.insulin}</td>
                <td className="px-3 py-2.5 text-right font-sans">
                  {e.readmit_30d === 1 ? (
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                      &lt;30 Days
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                      No
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500">
        <span>Showing {filtered.length} of {filtered.length} records</span>
        <div className="flex items-center space-x-1">
          <button disabled className="p-1.5 rounded border border-slate-200 dark:border-slate-700 opacity-50"><ChevronLeft className="w-3.5 h-3.5" /></button>
          <span className="px-2">Page {page} of 1</span>
          <button disabled className="p-1.5 rounded border border-slate-200 dark:border-slate-700 opacity-50"><ChevronRight className="w-3.5 h-3.5" /></button>
        </div>
      </div>
    </div>
  );
};
