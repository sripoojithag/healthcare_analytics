import React, { useState } from 'react';
import { BrainCircuit, Clock, Activity, Pill, ShieldAlert, Sparkles, CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-react';
import { predictRisk, PredictionResult } from '../../services/apiClient';

interface MLPredictorPanelProps {
  currentRole: string;
}

export const MLPredictorPanel: React.FC<MLPredictorPanelProps> = ({ currentRole }) => {
  const [stayDays, setStayDays] = useState<number>(4);
  const [labTests, setLabTests] = useState<number>(42);
  const [medCount, setMedCount] = useState<number>(15);
  const [priorInpatient, setPriorInpatient] = useState<number>(0);
  const [ageGroup, setAgeGroup] = useState<string>("[60-70)");
  const [gender, setGender] = useState<string>("Female");
  const [insulin, setInsulin] = useState<string>("Steady");

  const [prediction, setPrediction] = useState<PredictionResult>({
    readmission_probability: 0.442,
    predicted_class: 0,
    risk_tier: "Medium Risk",
    recommendation: "Schedule follow-up appointment within 7-14 days and review medication adherence."
  });
  const [isPredicting, setIsPredicting] = useState<boolean>(false);

  const handlePredict = async () => {
    setIsPredicting(true);
    const payload = {
      time_in_hospital: stayDays,
      num_lab_procedures: labTests,
      num_procedures: 1,
      num_medications: medCount,
      number_outpatient: 0,
      number_emergency: 0,
      number_inpatient: priorInpatient,
      number_diagnoses: 7,
      age: ageGroup,
      gender: gender,
      race: "Caucasian",
      insulin: insulin,
      diabetesMed: "Yes"
    };

    const res = await predictRisk(payload, currentRole);
    setPrediction(res);
    setIsPredicting(false);
  };

  const getTierBadge = (tier: string) => {
    if (tier === "High Risk") {
      return {
        bg: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30",
        icon: <AlertOctagon className="w-5 h-5 text-rose-600 dark:text-rose-400" />
      };
    }
    if (tier === "Medium Risk") {
      return {
        bg: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
        icon: <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
      };
    }
    return {
      bg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
      icon: <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
    };
  };

  const tierMeta = getTierBadge(prediction.risk_tier);

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 sm:p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
            <BrainCircuit className="w-5 h-5 text-indigo-500" />
            <span>Random Forest Model Inference Engine</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real inference via Scikit-learn pipeline (<code className="font-mono">models/readmission_pipeline_v1.joblib</code>)
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
          Leak-Free ML Pipeline
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Parameters */}
        <div className="lg:col-span-7 space-y-4">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
              <span className="flex items-center"><Clock className="w-3.5 h-3.5 mr-1 text-blue-500" /> Inpatient Stay (Days)</span>
              <span className="font-mono font-bold text-blue-600">{stayDays} days</span>
            </div>
            <input
              type="range"
              min={1}
              max={14}
              value={stayDays}
              onChange={(e) => setStayDays(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
              <span className="flex items-center"><Activity className="w-3.5 h-3.5 mr-1 text-emerald-500" /> Lab Procedures Volume</span>
              <span className="font-mono font-bold text-emerald-600">{labTests} tests</span>
            </div>
            <input
              type="range"
              min={1}
              max={100}
              value={labTests}
              onChange={(e) => setLabTests(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-600"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
              <span className="flex items-center"><Pill className="w-3.5 h-3.5 mr-1 text-purple-500" /> Prescribed Medications</span>
              <span className="font-mono font-bold text-purple-600">{medCount} meds</span>
            </div>
            <input
              type="range"
              min={1}
              max={50}
              value={medCount}
              onChange={(e) => setMedCount(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
          </div>

          <div className="grid grid-cols-3 gap-2 pt-1">
            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-1">Age Bracket</label>
              <select
                value={ageGroup}
                onChange={(e) => setAgeGroup(e.target.value)}
                className="w-full text-xs p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
              >
                {["[40-50)", "[50-60)", "[60-70)", "[70-80)", "[80-90)"].map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-1">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full text-xs p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
              >
                <option value="Female">Female</option>
                <option value="Male">Male</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-1">Insulin Regimen</label>
              <select
                value={insulin}
                onChange={(e) => setInsulin(e.target.value)}
                className="w-full text-xs p-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
              >
                <option value="No">No</option>
                <option value="Steady">Steady</option>
                <option value="Up">Up</option>
                <option value="Down">Down</option>
              </select>
            </div>
          </div>

          <button
            onClick={handlePredict}
            disabled={isPredicting}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/20 transition-all flex items-center justify-center space-x-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isPredicting ? "Computing Inference..." : "Run ML Risk Prediction"}</span>
          </button>
        </div>

        {/* Prediction Results Display */}
        <div className="lg:col-span-5 flex flex-col justify-between p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 space-y-4">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/60 dark:border-slate-700/60">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Predicted Risk Outcome
              </span>
              <span className="text-[11px] font-mono text-slate-400">RandomForest v1</span>
            </div>

            <div className="py-4 text-center space-y-2">
              <div className="flex justify-center">
                <div className={`p-3 rounded-full border ${tierMeta.bg}`}>
                  {tierMeta.icon}
                </div>
              </div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">
                {prediction.risk_tier}
              </div>
              <div className="text-sm font-semibold text-slate-600 dark:text-slate-400">
                Probability: <span className="font-mono text-slate-900 dark:text-white">{(prediction.readmission_probability * 100).toFixed(1)}%</span>
              </div>
            </div>

            <div className="space-y-1">
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    prediction.risk_tier === "High Risk" ? "bg-rose-500" :
                    prediction.risk_tier === "Medium Risk" ? "bg-amber-500" :
                    "bg-emerald-500"
                  }`}
                  style={{ width: `${prediction.readmission_probability * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>0% Low</span>
                <span>40% Med</span>
                <span>70%+ High</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs space-y-1">
            <span className="font-bold text-slate-900 dark:text-white block">Clinical Decision Support:</span>
            <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-[11px]">
              {prediction.recommendation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
