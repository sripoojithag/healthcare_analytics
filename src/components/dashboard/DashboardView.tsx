import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  BarChart3, 
  BrainCircuit, 
  ShieldCheck, 
  Table, 
  Shield, 
  Server,
  Database,
  AlertCircle
} from 'lucide-react';
import { 
  fetchKPIs, 
  fetchAgeCohorts, 
  fetchStayData, 
  fetchDiagnosisRisk, 
  fetchQualitySummary 
} from '../../services/apiClient';
import { useAuth } from '../../context/AuthContext';
import { KPICards } from './KPICards';
import { AgeCohortChart } from './AgeCohortChart';
import { StayCorrelationChart } from './StayCorrelationChart';
import { DiagnosisRiskTable } from './DiagnosisRiskTable';
import { DataQualityPanel } from './DataQualityPanel';
import { MLPredictorPanel } from './MLPredictorPanel';
import { EncountersTable } from './EncountersTable';
import { AuditTrailPanel } from './AuditTrailPanel';
import { DSAPanel } from './DSAPanel';

export const DashboardView: React.FC = () => {
  const { user } = useAuth();
  // Server-assigned role (defaults to 'viewer' if not authenticated)
  const currentRole = user?.role || 'viewer';

  const [activeSection, setActiveSection] = useState<'analytics' | 'dsa' | 'ml' | 'quality' | 'encounters' | 'audit'>('analytics');

  // React Query queries for warehouse data
  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['warehouse_kpis', currentRole],
    queryFn: () => fetchKPIs(currentRole)
  });

  const { data: ageData } = useQuery({
    queryKey: ['warehouse_age', currentRole],
    queryFn: () => fetchAgeCohorts(currentRole)
  });

  const { data: stayData } = useQuery({
    queryKey: ['warehouse_stay', currentRole],
    queryFn: () => fetchStayData(currentRole)
  });

  const { data: diagData } = useQuery({
    queryKey: ['warehouse_diag', currentRole],
    queryFn: () => fetchDiagnosisRisk(currentRole)
  });

  const { data: qualityData } = useQuery({
    queryKey: ['warehouse_quality'],
    queryFn: () => fetchQualitySummary()
  });

  const isWarehouseEmpty = kpis && kpis.total_encounters === 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Empty State Banner if warehouse active dataset was deleted */}
      {isWarehouseEmpty && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-200 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold">Active Warehouse Dataset Is Empty</h3>
            <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
              No clinical encounters are currently active in the warehouse. All analytical KPIs show zero values. If you are an administrator, visit the <strong>Admin Panel</strong> to upload and ingest a dataset.
            </p>
          </div>
        </div>
      )}

      {/* Top Status Bar: Authenticated Session Info */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 sm:p-5 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
              <Shield className="w-3.5 h-3.5 mr-1 text-blue-500" />
              Authenticated Session:
            </span>
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
              currentRole === 'admin' 
                ? 'bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300'
                : currentRole === 'analyst'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300'
                : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
            }`}>
              {currentRole} Role
            </span>
            {user && (
              <span className="text-xs text-slate-400 font-medium">({user.email})</span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {currentRole === 'viewer' && 'Viewer Role: Read-only aggregated KPIs and charts. Sensitive patient-level encounter listings and audit logs are restricted by server authorization.'}
            {currentRole === 'analyst' && 'Analyst Role: Full access to analytics, machine learning predictions, and de-identified/masked patient encounters.'}
            {currentRole === 'admin' && 'Admin Role: Full governance privileges including CSV uploads, dataset replacement, user management, and security audit inspection.'}
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-medium text-slate-500 dark:text-slate-400">
          <Database className="w-4 h-4 text-emerald-500" />
          <span>Star Schema DW: {kpis?.total_encounters?.toLocaleString() || 0} Encounters</span>
        </div>
      </div>

      {/* Sub-Navigation for Dashboard Modules */}
      <div className="flex overflow-x-auto space-x-2 border-b border-slate-200 dark:border-slate-800 pb-2 no-scrollbar">
        <button
          onClick={() => setActiveSection('analytics')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeSection === 'analytics'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Warehouse Analytics</span>
        </button>

        <button
          onClick={() => setActiveSection('dsa')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeSection === 'dsa'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50'
          }`}
        >
          <Server className="w-4 h-4" />
          <span>DSA Heap &amp; Graphs</span>
        </button>

        <button
          onClick={() => setActiveSection('ml')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeSection === 'ml'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50'
          }`}
        >
          <BrainCircuit className="w-4 h-4" />
          <span>ML Readmission Predictor</span>
        </button>

        <button
          onClick={() => setActiveSection('quality')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeSection === 'quality'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Data Quality &amp; Governance</span>
        </button>

        <button
          onClick={() => setActiveSection('encounters')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeSection === 'encounters'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50'
          }`}
        >
          <Table className="w-4 h-4" />
          <span>Masked Encounters</span>
        </button>

        <button
          onClick={() => setActiveSection('audit')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
            activeSection === 'audit'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>Security Audit Trail</span>
        </button>
      </div>

      {/* Module Views */}
      {activeSection === 'analytics' && (
        <div className="space-y-6">
          {kpis && <KPICards kpis={kpis} isLoading={kpisLoading} />}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {ageData && <AgeCohortChart data={ageData} />}
            {stayData && <StayCorrelationChart data={stayData} />}
          </div>
          {diagData && <DiagnosisRiskTable data={diagData} />}
        </div>
      )}

      {activeSection === 'dsa' && (
        <DSAPanel currentRole={currentRole} />
      )}

      {activeSection === 'ml' && (
        <MLPredictorPanel currentRole={currentRole} />
      )}

      {activeSection === 'quality' && qualityData && (
        <DataQualityPanel quality={qualityData} />
      )}

      {activeSection === 'encounters' && (
        <EncountersTable currentRole={currentRole} />
      )}

      {activeSection === 'audit' && (
        <AuditTrailPanel currentRole={currentRole} />
      )}
    </div>
  );
};
