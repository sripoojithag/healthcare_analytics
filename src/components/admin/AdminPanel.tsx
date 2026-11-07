import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ShieldAlert, 
  Users, 
  Database, 
  BrainCircuit, 
  FileText, 
  Activity, 
  Plus, 
  Trash2, 
  CheckCircle, 
  AlertTriangle, 
  Upload, 
  RefreshCw, 
  Key, 
  Sliders, 
  Lock, 
  Server
} from 'lucide-react';
import { 
  fetchAdminUsers, 
  createAdminUser, 
  updateUserRole, 
  updateUserStatus, 
  resetUserPassword,
  previewDatasetUpload,
  executeDatasetIngest,
  fetchActiveDatasetInfo,
  fetchIngestionHistory,
  deleteActiveDataset,
  fetchModelArtifacts,
  activateModelArtifact,
  fetchAdminAuditLogs,
  fetchSystemStatus,
  AdminUser,
  DatasetPreviewResult,
  ModelArtifactInfo,
  AuditLogEntry
} from '../../services/apiClient';
import { useAuth } from '../../context/AuthContext';

export const AdminPanel: React.FC = () => {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'users' | 'data' | 'models' | 'audit' | 'system'>('data');

  // User Management Form States
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [newUserRole, setNewUserRole] = useState<'admin' | 'analyst' | 'viewer'>('analyst');
  const [userError, setUserError] = useState<string | null>(null);
  const [userSuccess, setUserSuccess] = useState<string | null>(null);

  // Password reset modal state
  const [resettingUser, setResettingUser] = useState<AdminUser | null>(null);
  const [newPasswordValue, setNewPasswordValue] = useState('');

  // Data Ingestion States
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<DatasetPreviewResult | null>(null);
  const [ingestMode, setIngestMode] = useState<'append' | 'replace'>('append');
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [ingestStatusMessage, setIngestStatusMessage] = useState<string | null>(null);
  const [customMapping, setCustomMapping] = useState<Record<string, string>>({});

  // Dataset Deletion States
  const [deleteConfirmationInput, setDeleteConfirmationInput] = useState('');
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleteSuccess, setDeleteSuccess] = useState<string | null>(null);

  // --- React Queries ---
  const { data: users, refetch: refetchUsers } = useQuery({
    queryKey: ['admin_users'],
    queryFn: fetchAdminUsers,
    enabled: currentUser?.role === 'admin'
  });

  const { data: datasetInfo, refetch: refetchDatasetInfo } = useQuery({
    queryKey: ['admin_dataset_info'],
    queryFn: fetchActiveDatasetInfo,
    enabled: currentUser?.role === 'admin'
  });

  const { data: history, refetch: refetchHistory } = useQuery({
    queryKey: ['admin_ingest_history'],
    queryFn: fetchIngestionHistory,
    enabled: currentUser?.role === 'admin'
  });

  const { data: models, refetch: refetchModels } = useQuery({
    queryKey: ['admin_models'],
    queryFn: fetchModelArtifacts,
    enabled: currentUser?.role === 'admin'
  });

  const { data: auditLogs, refetch: refetchLogs } = useQuery({
    queryKey: ['admin_audit_logs'],
    queryFn: () => fetchAdminAuditLogs(100),
    enabled: currentUser?.role === 'admin'
  });

  const { data: sysStatus, refetch: refetchStatus } = useQuery({
    queryKey: ['admin_system_status'],
    queryFn: fetchSystemStatus,
    enabled: currentUser?.role === 'admin'
  });

  // --- Handlers: User Management ---
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setUserError(null);
    setUserSuccess(null);
    try {
      await createAdminUser({
        name: newUserName,
        email: newUserEmail,
        password: newUserPassword,
        role: newUserRole
      });
      setUserSuccess(`Created account for ${newUserEmail}`);
      setShowCreateUser(false);
      setNewUserName('');
      setNewUserEmail('');
      setNewUserPassword('');
      refetchUsers();
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  const handleRoleChange = async (userId: number, role: string) => {
    setUserError(null);
    try {
      await updateUserRole(userId, role);
      refetchUsers();
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  const handleStatusChange = async (userId: number, currentStatus: string) => {
    setUserError(null);
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    try {
      await updateUserStatus(userId, newStatus);
      refetchUsers();
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resettingUser) return;
    setUserError(null);
    try {
      await resetUserPassword(resettingUser.id, newPasswordValue);
      setUserSuccess(`Password reset successfully for ${resettingUser.email}`);
      setResettingUser(null);
      setNewPasswordValue('');
    } catch (err: any) {
      setUserError(err.message);
    }
  };

  // --- Handlers: Data Management & CSV Preview ---
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setIngestStatusMessage(null);
    try {
      const preview = await previewDatasetUpload(file);
      setPreviewData(preview);
      setCustomMapping(preview.suggested_column_mapping || {});
    } catch (err: any) {
      setIngestStatusMessage(`CSV Preview failed: ${err.message}`);
    }
  };

  const handleExecuteIngest = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setIngestStatusMessage(null);
    try {
      const res = await executeDatasetIngest(
        selectedFile,
        ingestMode,
        confirmReplace,
        customMapping
      );
      setIngestStatusMessage(
        `Success: ${res.inserted_records} inserted, ${res.duplicate_records} duplicates skipped, ${res.rejected_records} invalid records rejected. Total Active: ${res.total_active_records}`
      );
      setSelectedFile(null);
      setPreviewData(null);
      setConfirmReplace(false);
      refetchDatasetInfo();
      refetchHistory();
      queryClient.invalidateQueries({ queryKey: ['warehouse_kpis'] });
    } catch (err: any) {
      setIngestStatusMessage(`Ingestion error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDataset = async () => {
    setDeleteError(null);
    setDeleteSuccess(null);
    try {
      await deleteActiveDataset(deleteConfirmationInput);
      setDeleteSuccess('Active dataset successfully deleted. All analytics will now reflect an empty warehouse state.');
      setDeleteConfirmationInput('');
      refetchDatasetInfo();
      queryClient.invalidateQueries({ queryKey: ['warehouse_kpis'] });
      queryClient.invalidateQueries({ queryKey: ['warehouse_age'] });
      queryClient.invalidateQueries({ queryKey: ['warehouse_stay'] });
      queryClient.invalidateQueries({ queryKey: ['warehouse_diag'] });
    } catch (err: any) {
      setDeleteError(err.message);
    }
  };

  const handleActivateModel = async (modelName: string) => {
    try {
      await activateModelArtifact(modelName);
      refetchModels();
    } catch (err: any) {
      alert(`Model activation failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-purple-600/10 text-purple-600 dark:text-purple-400">
              <ShieldAlert className="w-5 h-5" />
            </span>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
              Platform Administration &amp; Data Ops
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Restricted to administrators. Manage user accounts, upload datasets, switch models, and inspect audit logs.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab('data')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              activeTab === 'data' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs' : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Data Ops</span>
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              activeTab === 'users' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs' : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Users</span>
          </button>
          <button
            onClick={() => setActiveTab('models')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              activeTab === 'models' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs' : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <BrainCircuit className="w-3.5 h-3.5" />
            <span>Models</span>
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              activeTab === 'audit' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs' : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Audit Logs</span>
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              activeTab === 'system' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs' : 'text-slate-600 dark:text-slate-400'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Health</span>
          </button>
        </div>
      </div>

      {/* Global Alerts */}
      {userError && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 rounded-xl text-xs flex items-center justify-between">
          <span>{userError}</span>
          <button onClick={() => setUserError(null)} className="font-bold ml-2">✕</button>
        </div>
      )}
      {userSuccess && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 rounded-xl text-xs flex items-center justify-between">
          <span>{userSuccess}</span>
          <button onClick={() => setUserSuccess(null)} className="font-bold ml-2">✕</button>
        </div>
      )}

      {/* --- TAB 1: DATA OPERATIONS --- */}
      {activeTab === 'data' && (
        <div className="space-y-6">
          {/* Active Dataset Metadata Card */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center">
              <Database className="w-4 h-4 mr-2 text-blue-500" />
              Active Dataset Status
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400">Dataset Identifier</div>
                <div className="text-base font-bold text-slate-900 dark:text-white mt-1">
                  {datasetInfo?.dataset_name || 'UCI Diabetes 130-US'}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">Version: {datasetInfo?.active_version || 'v1.0'}</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400">Active Records in Warehouse</div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                  {datasetInfo?.total_records?.toLocaleString() || 0}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  {datasetInfo?.total_records === 0 ? 'Empty Warehouse state' : 'Populated and serving analytics'}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <div className="text-xs text-slate-500 dark:text-slate-400">Last Warehouse Refresh</div>
                <div className="text-sm font-semibold text-slate-800 dark:text-slate-200 mt-1">
                  {datasetInfo?.last_updated_at ? new Date(datasetInfo.last_updated_at).toLocaleString() : 'Never'}
                </div>
                <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1">Transactional Integrity Verified</div>
              </div>
            </div>
          </div>

          {/* Ingestion & Upload Section */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                <Upload className="w-5 h-5 mr-2 text-indigo-500" />
                Upload &amp; Ingest Healthcare Dataset
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Ingest CSV files using schema validation, pre-flight column mapping, and configurable Append vs Replace modes.
              </p>
            </div>

            {/* File Input */}
            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-6 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
              <input
                type="file"
                accept=".csv"
                id="csv_upload"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="csv_upload" className="cursor-pointer flex flex-col items-center">
                <Upload className="w-8 h-8 text-slate-400 mb-2" />
                <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                  {selectedFile ? selectedFile.name : 'Select or drop a CSV file to inspect'}
                </span>
                <span className="text-xs text-slate-400 mt-1">Supports UCI Diabetes CSV and custom encounter exports</span>
              </label>
            </div>

            {/* CSV Schema Preview & Column Mapping */}
            {previewData && (
              <div className="space-y-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                      Pre-Flight Validation Preview
                    </h3>
                    <p className="text-xs text-slate-500">
                      Detected {previewData.detected_columns.length} columns in {previewData.filename}. Schema valid: {previewData.schema_valid ? 'Yes' : 'Requires mapping'}
                    </p>
                  </div>
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                    previewData.schema_valid ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                  }`}>
                    {previewData.schema_valid ? 'Schema Compliant' : 'Column Mapping Required'}
                  </span>
                </div>

                {/* Detected Preview Records */}
                <div className="overflow-x-auto max-h-48 border border-slate-200 dark:border-slate-700 rounded-lg">
                  <table className="min-w-full text-xs divide-y divide-slate-200 dark:divide-slate-800">
                    <thead className="bg-slate-100 dark:bg-slate-800">
                      <tr>
                        {previewData.detected_columns.slice(0, 8).map((col) => (
                          <th key={col} className="px-3 py-1.5 text-left font-semibold text-slate-600 dark:text-slate-400">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {previewData.preview_records.slice(0, 3).map((row, idx) => (
                        <tr key={idx}>
                          {previewData.detected_columns.slice(0, 8).map((col) => (
                            <td key={col} className="px-3 py-1.5 whitespace-nowrap text-slate-700 dark:text-slate-300">
                              {String(row[col] ?? '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Ingestion Mode Choice */}
                <div className="pt-2">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Ingestion Mode:
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <label className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      ingestMode === 'append'
                        ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/30'
                        : 'border-slate-200 dark:border-slate-700'
                    }`}>
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          name="ingest_mode"
                          checked={ingestMode === 'append'}
                          onChange={() => setIngestMode('append')}
                          className="text-blue-600"
                        />
                        <span className="text-xs font-bold text-slate-900 dark:text-white">Append Mode (Default)</span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 pl-5">
                        Appends new encounters. Automatically deduplicates using `encounter_id` to prevent duplicate clinical records.
                      </p>
                    </label>

                    <label className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      ingestMode === 'replace'
                        ? 'border-amber-500 bg-amber-50/50 dark:bg-amber-950/30'
                        : 'border-slate-200 dark:border-slate-700'
                    }`}>
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          name="ingest_mode"
                          checked={ingestMode === 'replace'}
                          onChange={() => setIngestMode('replace')}
                          className="text-amber-600"
                        />
                        <span className="text-xs font-bold text-slate-900 dark:text-white">Replace Active Dataset</span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 pl-5">
                        Transactionally stages and replaces all active encounters with new file content. Requires explicit confirmation below.
                      </p>
                    </label>
                  </div>
                </div>

                {/* Explicit confirmation checkbox if replace mode */}
                {ingestMode === 'replace' && (
                  <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 rounded-xl">
                    <label className="flex items-center space-x-2 cursor-pointer text-xs font-semibold text-amber-900 dark:text-amber-200">
                      <input
                        type="checkbox"
                        checked={confirmReplace}
                        onChange={(e) => setConfirmReplace(e.target.checked)}
                        className="rounded border-amber-400 text-amber-600 focus:ring-amber-500"
                      />
                      <span>I confirm I want to replace the active dataset in the warehouse</span>
                    </label>
                  </div>
                )}

                {/* Execute Button */}
                <button
                  onClick={handleExecuteIngest}
                  disabled={isUploading || (ingestMode === 'replace' && !confirmReplace)}
                  className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Processing ETL &amp; Ingestion...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Execute {ingestMode.toUpperCase()} Ingestion</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {ingestStatusMessage && (
              <div className="p-3 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-blue-800 dark:text-blue-300 rounded-xl text-xs">
                {ingestStatusMessage}
              </div>
            )}
          </div>

          {/* Ingestion History Table */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center">
              <FileText className="w-4 h-4 mr-2 text-indigo-500" />
              Ingestion Job History
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs divide-y divide-slate-200 dark:divide-slate-800">
                <thead>
                  <tr className="text-slate-500 dark:text-slate-400">
                    <th className="py-2 text-left font-semibold">Job ID</th>
                    <th className="py-2 text-left font-semibold">Filename</th>
                    <th className="py-2 text-left font-semibold">Mode</th>
                    <th className="py-2 text-left font-semibold">Inserted</th>
                    <th className="py-2 text-left font-semibold">Duplicates</th>
                    <th className="py-2 text-left font-semibold">Rejected</th>
                    <th className="py-2 text-left font-semibold">Status</th>
                    <th className="py-2 text-left font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {history && history.length > 0 ? (
                    history.map((job: any) => (
                      <tr key={job.job_id}>
                        <td className="py-2 font-mono text-slate-700 dark:text-slate-300">{job.job_id.slice(0, 8)}...</td>
                        <td className="py-2 text-slate-900 dark:text-white font-medium">{job.filename}</td>
                        <td className="py-2 uppercase font-semibold text-slate-600 dark:text-slate-400">{job.mode}</td>
                        <td className="py-2 text-emerald-600 dark:text-emerald-400 font-semibold">{job.inserted_records}</td>
                        <td className="py-2 text-amber-600 dark:text-amber-400">{job.duplicate_records}</td>
                        <td className="py-2 text-rose-600 dark:text-rose-400">{job.rejected_records}</td>
                        <td className="py-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            job.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300' : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                          }`}>
                            {job.status}
                          </span>
                        </td>
                        <td className="py-2 text-slate-400">{new Date(job.created_at).toLocaleString()}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="py-4 text-center text-slate-400">No ingestion jobs logged yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Danger Zone: Dataset Deletion */}
          <div className="bg-rose-50/50 dark:bg-rose-950/20 rounded-2xl p-6 border border-rose-200 dark:border-rose-900">
            <h2 className="text-sm font-bold uppercase tracking-wider text-rose-700 dark:text-rose-400 flex items-center mb-1">
              <AlertTriangle className="w-4 h-4 mr-1.5" />
              Danger Zone: Delete Active Dataset
            </h2>
            <p className="text-xs text-rose-600 dark:text-rose-400 mb-4">
              Purges all clinical encounters and active analytics records from the warehouse while preserving system audit logs and historical ingestion manifests. Analytics dashboards will safely render an empty state.
            </p>

            <div className="max-w-md space-y-3">
              <div>
                <label className="block text-xs font-semibold text-rose-800 dark:text-rose-300 mb-1">
                  Type <span className="font-mono bg-rose-100 dark:bg-rose-900/60 px-1 py-0.5 rounded">DELETE ACTIVE DATASET</span> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteConfirmationInput}
                  onChange={(e) => setDeleteConfirmationInput(e.target.value)}
                  placeholder="DELETE ACTIVE DATASET"
                  className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-900 border border-rose-300 dark:border-rose-800 rounded-xl font-mono focus:ring-2 focus:ring-rose-500 focus:outline-none"
                />
              </div>

              {deleteError && <p className="text-xs text-rose-600 font-semibold">{deleteError}</p>}
              {deleteSuccess && <p className="text-xs text-emerald-600 font-semibold">{deleteSuccess}</p>}

              <button
                onClick={handleDeleteDataset}
                disabled={deleteConfirmationInput !== 'DELETE ACTIVE DATASET'}
                className="py-2 px-4 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs shadow-sm transition-all disabled:opacity-40"
              >
                Permanently Delete Active Dataset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- TAB 2: USER MANAGEMENT --- */}
      {activeTab === 'users' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                <Users className="w-5 h-5 mr-2 text-blue-500" />
                User &amp; Access Governance
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Server-enforced RBAC. Built-in safeguards protect against self-demotion and last-administrator lockout.
              </p>
            </div>
            <button
              onClick={() => setShowCreateUser(!showCreateUser)}
              className="py-2 px-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm flex items-center space-x-1.5 self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              <span>{showCreateUser ? 'Cancel' : 'Create User'}</span>
            </button>
          </div>

          {/* Create User Form */}
          {showCreateUser && (
            <form onSubmit={handleCreateUser} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Add New Healthcare User Account
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={newUserName}
                    onChange={(e) => setNewUserName(e.target.value)}
                    placeholder="Dr. Gregory House"
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={newUserEmail}
                    onChange={(e) => setNewUserEmail(e.target.value)}
                    placeholder="ghouse@healthcare.local"
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Temporary Password</label>
                  <input
                    type="password"
                    required
                    value={newUserPassword}
                    onChange={(e) => setNewUserPassword(e.target.value)}
                    placeholder="Min 8 characters"
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Assigned Role</label>
                  <select
                    value={newUserRole}
                    onChange={(e: any) => setNewUserRole(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg"
                  >
                    <option value="viewer">Viewer (Read-only)</option>
                    <option value="analyst">Analyst (ML &amp; Data)</option>
                    <option value="admin">Admin (Full Control)</option>
                  </select>
                </div>
              </div>
              <button
                type="submit"
                className="py-2 px-4 rounded-lg bg-blue-600 text-white font-semibold text-xs"
              >
                Save User
              </button>
            </form>
          )}

          {/* Password Reset Modal */}
          {resettingUser && (
            <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
              <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-sm w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Reset Password for {resettingUser.name}
                </h3>
                <p className="text-xs text-slate-500">Provide a new password with at least 8 characters.</p>
                <form onSubmit={handleResetPassword} className="space-y-3">
                  <input
                    type="password"
                    required
                    value={newPasswordValue}
                    onChange={(e) => setNewPasswordValue(e.target.value)}
                    placeholder="New Secure Password"
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg"
                  />
                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setResettingUser(null)}
                      className="px-3 py-1.5 text-xs text-slate-600 dark:text-slate-400"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg font-semibold"
                    >
                      Update Password
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* User Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs divide-y divide-slate-200 dark:divide-slate-800">
              <thead>
                <tr className="text-slate-500 dark:text-slate-400">
                  <th className="py-2.5 text-left font-semibold">User</th>
                  <th className="py-2.5 text-left font-semibold">Role</th>
                  <th className="py-2.5 text-left font-semibold">Account Status</th>
                  <th className="py-2.5 text-left font-semibold">Last Login</th>
                  <th className="py-2.5 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {users && users.map((u) => {
                  const isCurrentAdmin = currentUser?.id === u.id || currentUser?.email === u.email;
                  return (
                    <tr key={u.id}>
                      <td className="py-3">
                        <div className="font-semibold text-slate-900 dark:text-white flex items-center space-x-1.5">
                          <span>{u.name}</span>
                          {isCurrentAdmin && (
                            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
                              You
                            </span>
                          )}
                        </div>
                        <div className="text-slate-500 text-[11px]">{u.email}</div>
                      </td>
                      <td className="py-3">
                        <select
                          value={u.role}
                          disabled={isCurrentAdmin}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          className={`text-xs px-2 py-1 rounded-md border font-semibold ${
                            u.role === 'admin'
                              ? 'bg-purple-50 text-purple-800 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800'
                              : u.role === 'analyst'
                              ? 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800'
                              : 'bg-slate-50 text-slate-800 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700'
                          }`}
                        >
                          <option value="admin">Admin</option>
                          <option value="analyst">Analyst</option>
                          <option value="viewer">Viewer</option>
                        </select>
                      </td>
                      <td className="py-3">
                        <button
                          disabled={isCurrentAdmin}
                          onClick={() => handleStatusChange(u.id, u.status)}
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold transition-colors ${
                            u.status === 'active'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 hover:bg-emerald-200'
                              : 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 hover:bg-rose-200'
                          }`}
                        >
                          {u.status.toUpperCase()}
                        </button>
                      </td>
                      <td className="py-3 text-slate-400">
                        {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}
                      </td>
                      <td className="py-3 text-right">
                        <button
                          onClick={() => setResettingUser(u)}
                          className="px-2 py-1 rounded text-[11px] font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors inline-flex items-center space-x-1"
                        >
                          <Key className="w-3 h-3" />
                          <span>Reset Password</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* --- TAB 3: MODEL MANAGEMENT --- */}
      {activeTab === 'models' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
              <BrainCircuit className="w-5 h-5 mr-2 text-indigo-500" />
              Machine Learning Model Artifacts
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Inspect model metadata, test metrics, and activate versioned inference pipelines without code redeployment.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {models && models.map((m) => (
              <div
                key={m.name}
                className={`p-5 rounded-2xl border transition-all ${
                  m.is_active
                    ? 'border-indigo-500 bg-indigo-50/30 dark:bg-indigo-950/20 shadow-xs'
                    : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">{m.name}</h3>
                    <p className="text-xs text-slate-400">{m.algorithm} • Version {m.version}</p>
                  </div>
                  {m.is_active ? (
                    <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 flex items-center space-x-1">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      <span>Active Inference Model</span>
                    </span>
                  ) : (
                    <button
                      onClick={() => handleActivateModel(m.name)}
                      className="px-3 py-1 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-200 transition-colors"
                    >
                      Set as Active
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 dark:border-slate-700 text-center">
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Accuracy</div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white">{(m.accuracy * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">F1-Score</div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white">{(m.f1_score * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">ROC-AUC</div>
                    <div className="text-sm font-bold text-indigo-600 dark:text-indigo-400">{(m.roc_auc).toFixed(3)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- TAB 4: AUDIT LOGS --- */}
      {activeTab === 'audit' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
                <FileText className="w-5 h-5 mr-2 text-blue-500" />
                Immutable Administrative Audit Trail
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Append-only log recording authentications, user modifications, dataset replacements, and model activations.
              </p>
            </div>
            <button
              onClick={() => refetchLogs()}
              className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 transition-colors"
              title="Refresh logs"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="overflow-x-auto max-h-[500px]">
            <table className="min-w-full text-xs divide-y divide-slate-200 dark:divide-slate-800">
              <thead className="sticky top-0 bg-slate-50 dark:bg-slate-900">
                <tr className="text-slate-500 dark:text-slate-400">
                  <th className="py-2 text-left font-semibold">Timestamp</th>
                  <th className="py-2 text-left font-semibold">User</th>
                  <th className="py-2 text-left font-semibold">Role</th>
                  <th className="py-2 text-left font-semibold">Action</th>
                  <th className="py-2 text-left font-semibold">Resource</th>
                  <th className="py-2 text-left font-semibold">Status</th>
                  <th className="py-2 text-left font-semibold">Client IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono text-[11px]">
                {auditLogs && auditLogs.map((log: AuditLogEntry) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-2 text-slate-400 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="py-2 text-slate-700 dark:text-slate-300">{log.user_id}</td>
                    <td className="py-2 uppercase font-semibold text-slate-500">{log.role}</td>
                    <td className="py-2 font-bold text-slate-900 dark:text-white">{log.action}</td>
                    <td className="py-2 text-slate-500 truncate max-w-xs">{log.resource}</td>
                    <td className="py-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        log.status === 'SUCCESS' ? 'text-emerald-700 dark:text-emerald-400' : 'text-rose-700 dark:text-rose-400'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="py-2 text-slate-400">{log.client_ip}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* --- TAB 5: SYSTEM HEALTH --- */}
      {activeTab === 'system' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center">
              <Server className="w-5 h-5 mr-2 text-emerald-500" />
              Service Status &amp; Warehouse Health
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Live heartbeat and subsystem readiness for backend, SQLite/PostgreSQL warehouse, and ML inference.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center space-x-2 text-xs font-bold text-slate-500 mb-2">
                <Database className="w-4 h-4 text-blue-500" />
                <span>Warehouse Database</span>
              </div>
              <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 capitalize">
                {sysStatus?.services?.warehouse_db?.status || 'Online'}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {sysStatus?.services?.warehouse_db?.total_encounters?.toLocaleString() || 0} encounters loaded
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center space-x-2 text-xs font-bold text-slate-500 mb-2">
                <BrainCircuit className="w-4 h-4 text-purple-500" />
                <span>Model Pipeline</span>
              </div>
              <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 capitalize">
                {sysStatus?.services?.model_inference?.status || 'Online'}
              </div>
              <div className="text-xs text-slate-500 mt-1 truncate">
                Active: {sysStatus?.services?.model_inference?.active_model || 'RandomForest'}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center space-x-2 text-xs font-bold text-slate-500 mb-2">
                <Lock className="w-4 h-4 text-indigo-500" />
                <span>Auth &amp; RBAC Service</span>
              </div>
              <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 capitalize">
                {sysStatus?.services?.auth_service?.status || 'Active'}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {sysStatus?.services?.auth_service?.total_users || 3} registered accounts
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
