import React from 'react';
import { Users, Activity, Clock, Pill, AlertOctagon, TrendingUp, CheckCircle } from 'lucide-react';
import { KPIStats } from '../../services/apiClient';

interface KPICardsProps {
  kpis: KPIStats;
  isLoading?: boolean;
}

export const KPICards: React.FC<KPICardsProps> = ({ kpis, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse border border-slate-200 dark:border-slate-700/60" />
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: "Total Encounters",
      value: kpis.total_encounters.toLocaleString(),
      subtitle: `${kpis.unique_patients.toLocaleString()} unique patients`,
      icon: <Users className="w-4 h-4 text-blue-500" />,
      color: "border-blue-200 dark:border-blue-900/50"
    },
    {
      title: "30-Day Readmission",
      value: `${kpis.readmitted_30d_rate_pct}%`,
      subtitle: `${kpis.readmitted_30d_count.toLocaleString()} patients < 30d`,
      icon: <AlertOctagon className="w-4 h-4 text-rose-500" />,
      color: "border-rose-200 dark:border-rose-900/50"
    },
    {
      title: "Overall Readmission",
      value: `${kpis.total_readmission_rate_pct}%`,
      subtitle: `${kpis.total_readmissions_count.toLocaleString()} readmitted total`,
      icon: <TrendingUp className="w-4 h-4 text-amber-500" />,
      color: "border-amber-200 dark:border-amber-900/50"
    },
    {
      title: "Avg Length of Stay",
      value: `${kpis.avg_length_of_stay_days} d`,
      subtitle: "Inpatient stay duration",
      icon: <Clock className="w-4 h-4 text-indigo-500" />,
      color: "border-indigo-200 dark:border-indigo-900/50"
    },
    {
      title: "Avg Lab Tests",
      value: kpis.avg_lab_procedures.toString(),
      subtitle: "Procedures per visit",
      icon: <Activity className="w-4 h-4 text-emerald-500" />,
      color: "border-emerald-200 dark:border-emerald-900/50"
    },
    {
      title: "Avg Medications",
      value: kpis.avg_medications_per_encounter.toString(),
      subtitle: "Medications per visit",
      icon: <Pill className="w-4 h-4 text-purple-500" />,
      color: "border-purple-200 dark:border-purple-900/50"
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
      {cards.map((c, idx) => (
        <div
          key={idx}
          className={`p-4 rounded-xl bg-white dark:bg-slate-900 border ${c.color} shadow-xs space-y-1.5 transition-all hover:shadow-md`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              {c.title}
            </span>
            <div className="p-1 rounded-md bg-slate-50 dark:bg-slate-800">
              {c.icon}
            </div>
          </div>
          <div className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white">
            {c.value}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
            {c.subtitle}
          </p>
        </div>
      ))}
    </div>
  );
};
