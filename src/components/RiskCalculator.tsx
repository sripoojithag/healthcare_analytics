import React, { useState } from 'react';
import { 
  Activity, 
  Clock, 
  Pill, 
  AlertTriangle, 
  CheckCircle, 
  AlertOctagon, 
  Sparkles, 
  RefreshCw, 
  ExternalLink,
  Info,
  ShieldCheck,
  Stethoscope
} from 'lucide-react';
import { REPO_META } from '../data/repoData';

export const RiskCalculator: React.FC = () => {
  const [timeInHospital, setTimeInHospital] = useState<number>(4);
  const [numLabProcedures, setNumLabProcedures] = useState<number>(38);
  const [numMedications, setNumMedications] = useState<number>(14);
  const [ageGroup, setAgeGroup] = useState<string>('60-70');

  const totalScore = timeInHospital + numLabProcedures + numMedications;

  // Exact rule from app/application.py:
  // if score > 80 -> High Risk
  // elif score > 40 -> Medium Risk
  // else -> Low Risk
  let riskLevel: 'Low' | 'Medium' | 'High' = 'Low';
  if (totalScore > 80) {
    riskLevel = 'High';
  } else if (totalScore > 40) {
    riskLevel = 'Medium';
  } else {
    riskLevel = 'Low';
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'High':
        return {
          bg: 'bg-rose-500/10 dark:bg-rose-950/40',
          border: 'border-rose-500/30',
          text: 'text-rose-600 dark:text-rose-400',
          badge: 'bg-rose-600 text-white',
          bar: 'bg-rose-500',
          icon: <AlertOctagon className="w-6 h-6 text-rose-600 dark:text-rose-400" />
        };
      case 'Medium':
        return {
          bg: 'bg-amber-500/10 dark:bg-amber-950/40',
          border: 'border-amber-500/30',
          text: 'text-amber-600 dark:text-amber-400',
          badge: 'bg-amber-500 text-slate-900',
          bar: 'bg-amber-500',
          icon: <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
        };
      default:
        return {
          bg: 'bg-emerald-500/10 dark:bg-emerald-950/40',
          border: 'border-emerald-500/30',
          text: 'text-emerald-600 dark:text-emerald-400',
          badge: 'bg-emerald-600 text-white',
          bar: 'bg-emerald-500',
          icon: <CheckCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
        };
    }
  };

  const riskMeta = getRiskColor(riskLevel);

  const applyPreset = (preset: 'low' | 'med' | 'high') => {
    if (preset === 'low') {
      setTimeInHospital(2);
      setNumLabProcedures(15);
      setNumMedications(8);
      setAgeGroup('30-40');
    } else if (preset === 'med') {
      setTimeInHospital(4);
      setNumLabProcedures(42);
      setNumMedications(18);
      setAgeGroup('60-70');
    } else {
      setTimeInHospital(10);
      setNumLabProcedures(68);
      setNumMedications(28);
      setAgeGroup('70-80');
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-800 mb-2">
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Interactive Model Simulation</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">
            Hospital Readmission Risk Predictor
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Direct reproduction of the Streamlit application logic from <code className="text-blue-600 dark:text-blue-400 font-mono">app/application.py</code> in the repository, calculating risk thresholds using inpatient stay duration, laboratory test procedures, and medication quantity.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={REPO_META.liveDemoUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center space-x-1 px-3 py-2 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-all border border-slate-200 dark:border-slate-700"
          >
            <span>Live Streamlit Demo</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Preset Quick Selectors */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 mr-2 flex items-center">
          <Sparkles className="w-3.5 h-3.5 mr-1 text-blue-500" /> Clinical Presets:
        </span>
        <button
          onClick={() => applyPreset('low')}
          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100 transition-all"
        >
          Routine Day Procedure (Low)
        </button>
        <button
          onClick={() => applyPreset('med')}
          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 hover:bg-amber-100 transition-all"
        >
          Moderate Stay Inpatient (Medium)
        </button>
        <button
          onClick={() => applyPreset('high')}
          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 transition-all"
        >
          Complex Multi-Condition Case (High)
        </button>
      </div>

      {/* Two Column Layout: Controls & Risk Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sliders Input Form */}
        <div className="lg:col-span-7 bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-3 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Patient Input Parameters
            </h3>
            <span className="text-xs text-slate-400">Streamlit Slider Ranges</span>
          </div>

          {/* Time in Hospital Slider (1 to 14 days) */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm font-medium">
              <span className="text-slate-700 dark:text-slate-300 flex items-center">
                <Clock className="w-4 h-4 mr-1.5 text-blue-500" />
                Time in Hospital (Days)
              </span>
              <span className="font-mono font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50 px-2.5 py-0.5 rounded border border-blue-200 dark:border-blue-900">
                {timeInHospital} {timeInHospital === 1 ? 'day' : 'days'}
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={14}
              value={timeInHospital}
              onChange={(e) => setTimeInHospital(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>1 day</span>
              <span>7 days</span>
              <span>14 days</span>
            </div>
          </div>

          {/* Lab Procedures Slider (1 to 100) */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm font-medium">
              <span className="text-slate-700 dark:text-slate-300 flex items-center">
                <Activity className="w-4 h-4 mr-1.5 text-emerald-500" />
                Number of Lab Procedures
              </span>
              <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2.5 py-0.5 rounded border border-emerald-200 dark:border-emerald-900">
                {numLabProcedures} procedures
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={100}
              value={numLabProcedures}
              onChange={(e) => setNumLabProcedures(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-600"
            />
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>1 procedure</span>
              <span>50 procedures</span>
              <span>100 procedures</span>
            </div>
          </div>

          {/* Number of Medications Slider (1 to 50) */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-sm font-medium">
              <span className="text-slate-700 dark:text-slate-300 flex items-center">
                <Pill className="w-4 h-4 mr-1.5 text-purple-500" />
                Number of Medications
              </span>
              <span className="font-mono font-bold text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/50 px-2.5 py-0.5 rounded border border-purple-200 dark:border-purple-900">
                {numMedications} meds
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={50}
              value={numMedications}
              onChange={(e) => setNumMedications(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>1 medication</span>
              <span>25 medications</span>
              <span>50 medications</span>
            </div>
          </div>

          {/* Age Cohort Filter (from SQL Analysis) */}
          <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400 flex items-center">
              Age Cohort (Reference Demographics)
            </label>
            <div className="grid grid-cols-4 gap-1.5">
              {['20-40', '40-60', '60-70', '70-80'].map((age) => (
                <button
                  key={age}
                  type="button"
                  onClick={() => setAgeGroup(age)}
                  className={`text-xs py-1.5 px-2 rounded-lg font-medium border text-center transition-all ${
                    ageGroup === age
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-100'
                  }`}
                >
                  {age} yrs
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Prediction Results Gauge */}
        <div className="lg:col-span-5 bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-3 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                Prediction Assessment
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-medium">
                RF 88% Accuracy
              </span>
            </div>

            {/* Classification Card */}
            <div className={`p-6 rounded-2xl border ${riskMeta.bg} ${riskMeta.border} text-center space-y-3`}>
              <div className="flex justify-center">
                <div className="p-3 rounded-full bg-white dark:bg-slate-900 shadow-sm">
                  {riskMeta.icon}
                </div>
              </div>
              <div>
                <span className="text-xs uppercase font-bold tracking-widest text-slate-500 dark:text-slate-400">
                  Calculated Risk Tier
                </span>
                <div className={`text-2xl sm:text-3xl font-extrabold mt-1 ${riskMeta.text}`}>
                  {riskLevel} Risk of Readmission
                </div>
              </div>

              {/* Progress gauge */}
              <div className="space-y-1.5 pt-2">
                <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <span>Score: {totalScore} pts</span>
                  <span>Threshold: 80 pts</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 h-3 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${riskMeta.bar} transition-all duration-300`}
                    style={{ width: `${Math.min(100, (totalScore / 164) * 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>0 (Low)</span>
                  <span>40 (Medium)</span>
                  <span>80+ (High)</span>
                </div>
              </div>
            </div>

            {/* Clinical Recommendation */}
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 text-xs space-y-1.5">
              <span className="font-bold text-slate-900 dark:text-white flex items-center">
                <ShieldCheck className="w-3.5 h-3.5 mr-1 text-blue-600" />
                Hospital Workflow Recommendation:
              </span>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                {riskLevel === 'High' && "Flag patient for mandatory 48-hour post-discharge telemedicine check, comprehensive medication reconciliation, and home healthcare nursing referral."}
                {riskLevel === 'Medium' && "Schedule a primary care provider follow-up within 7 to 14 days and provide simplified discharge instructions on medication adherence."}
                {riskLevel === 'Low' && "Standard post-discharge follow-up care protocol with normal clinic scheduling."}
              </p>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 flex items-start space-x-1.5">
            <Info className="w-3.5 h-3.5 text-blue-500 flex-shrink-0 mt-0.5" />
            <span>
              Logic verified from repo file: <code className="text-slate-600 dark:text-slate-300 font-mono">app/application.py</code> line 17: <code className="text-blue-500 font-mono">score = (time_in_hospital + num_lab_procedures + num_medications)</code>.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
