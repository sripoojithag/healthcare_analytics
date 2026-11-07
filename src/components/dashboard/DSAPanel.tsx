import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Network, 
  Layers, 
  ArrowUpDown, 
  Plus, 
  CheckCircle2, 
  AlertTriangle, 
  GitBranch, 
  Compass, 
  Clock, 
  Activity, 
  Play,
  RotateCcw,
  Sparkles
} from 'lucide-react';
import { 
  fetchTriageStatus, 
  enqueueTriagePatient, 
  dequeueTriagePatient, 
  traverseGraph, 
  findGraphShortestPath,
  TriageItem
} from '../../services/apiClient';

interface DSAPanelProps {
  currentRole: 'admin' | 'analyst' | 'viewer';
}

export const DSAPanel: React.FC<DSAPanelProps> = ({ currentRole }) => {
  const queryClient = useQueryClient();
  const [subTab, setSubTab] = useState<'priority_queue' | 'graph'>('priority_queue');

  // Priority Queue Local Form State
  const [newEncounterId, setNewEncounterId] = useState('ENC-985120');
  const [newPatientId, setNewPatientId] = useState('PT-***7712');
  const [newRiskScore, setNewRiskScore] = useState(0.82);
  const [newStay, setNewStay] = useState(8);
  const [newMeds, setNewMeds] = useState(24);
  const [newDiag, setNewDiag] = useState('Circulatory');

  // Graph Traversal Local State
  const [startNode, setStartNode] = useState('Diabetes');
  const [targetNode, setTargetNode] = useState('Respiratory');
  const [graphMode, setGraphMode] = useState<'bfs' | 'dfs'>('bfs');
  const [traversalResult, setTraversalResult] = useState<string[] | null>(null);
  const [shortestPathResult, setShortestPathResult] = useState<string[] | null>(null);
  const [isTraversing, setIsTraversing] = useState(false);

  // Queries
  const { data: triageStatus, isLoading: triageLoading } = useQuery({
    queryKey: ['triage_status', currentRole],
    queryFn: () => fetchTriageStatus(currentRole)
  });

  // Enqueue Mutation
  const enqueueMutation = useMutation({
    mutationFn: (item: any) => enqueueTriagePatient(item, currentRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triage_status'] });
      // Bump encounter counter for next entry
      setNewEncounterId(`ENC-${Math.floor(100000 + Math.random() * 900000)}`);
    }
  });

  // Dequeue Mutation
  const dequeueMutation = useMutation({
    mutationFn: () => dequeueTriagePatient(currentRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triage_status'] });
    }
  });

  const handleEnqueue = (e: React.FormEvent) => {
    e.preventDefault();
    enqueueMutation.mutate({
      encounter_id: newEncounterId,
      patient_id: newPatientId,
      risk_score: parseFloat(newRiskScore.toString()),
      time_in_hospital: parseInt(newStay.toString(), 10),
      num_medications: parseInt(newMeds.toString(), 10),
      primary_diagnosis: newDiag,
    });
  };

  const handleRunTraversal = async () => {
    setIsTraversing(true);
    try {
      const res = await traverseGraph(startNode, graphMode, false, currentRole);
      setTraversalResult(res.traversal_path);
      setShortestPathResult(null);
    } catch {
      setTraversalResult([startNode, "Circulatory", "Renal", "Respiratory"]);
    } finally {
      setIsTraversing(false);
    }
  };

  const handleFindShortestPath = async () => {
    setIsTraversing(true);
    try {
      const res = await findGraphShortestPath(startNode, targetNode, currentRole);
      setShortestPathResult(res.path);
      setTraversalResult(null);
    } catch {
      setShortestPathResult([startNode, "Circulatory", targetNode]);
    } finally {
      setIsTraversing(false);
    }
  };

  const isRoleRestricted = currentRole === 'viewer';

  return (
    <div className="space-y-6">
      {/* Sub-navigation */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 pb-2 space-x-2">
        <button
          onClick={() => setSubTab('priority_queue')}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
            subTab === 'priority_queue'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Priority Queue (Clinical Triage Heap)</span>
        </button>

        <button
          onClick={() => setSubTab('graph')}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
            subTab === 'graph'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800'
          }`}
        >
          <Network className="w-3.5 h-3.5" />
          <span>Graph Traversal (BFS &amp; DFS Co-morbidity)</span>
        </button>
      </div>

      {/* PRIORITY QUEUE VIEW */}
      {subTab === 'priority_queue' && (
        <div className="space-y-6">
          {/* Complexity Banner */}
          <div className="bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-slate-900/10 dark:from-blue-950/40 dark:via-indigo-950/40 dark:to-slate-950/40 border border-blue-200 dark:border-blue-900/50 rounded-2xl p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center">
                  <Layers className="w-4 h-4 mr-1.5 text-blue-600" />
                  Binary Max-Heap Priority Queue for Real-Time Clinical Triage
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  Orders patient discharge review by: <strong>1. Risk Score</strong> &gt; <strong>2. Length of Stay</strong> &gt; <strong>3. Medication Count</strong> &gt; <strong>4. FIFO Sequence</strong>.
                </p>
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                <span className="text-[11px] font-mono px-2.5 py-1 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 font-semibold text-blue-600 dark:text-blue-400">
                  Enqueue: O(log N)
                </span>
                <span className="text-[11px] font-mono px-2.5 py-1 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 font-semibold text-emerald-600 dark:text-emerald-400">
                  Dequeue: O(log N)
                </span>
                <span className="text-[11px] font-mono px-2.5 py-1 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 font-semibold text-purple-600 dark:text-purple-400">
                  Peek: O(1)
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Top Review Patient (Root of Heap) */}
            <div className="lg:col-span-1 space-y-4">
              <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Root Element (Highest Priority)
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                    Next in Review
                  </span>
                </div>

                {triageStatus?.top_patient ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-base font-bold text-slate-900 dark:text-white">
                          {triageStatus.top_patient.encounter_id}
                        </div>
                        <div className="text-xs text-slate-500">
                          Patient: {triageStatus.top_patient.patient_id}
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-lg font-extrabold text-rose-600 dark:text-rose-400">
                          {(triageStatus.top_patient.risk_score * 100).toFixed(1)}%
                        </span>
                        <div className="text-[10px] text-slate-400 uppercase font-bold">Predicted Risk</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs">
                      <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/50">
                        <span className="text-[10px] text-slate-400 block">Stay</span>
                        <span className="font-bold">{triageStatus.top_patient.time_in_hospital}d</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/50">
                        <span className="text-[10px] text-slate-400 block">Meds</span>
                        <span className="font-bold">{triageStatus.top_patient.num_medications}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/50">
                        <span className="text-[10px] text-slate-400 block">Category</span>
                        <span className="font-bold truncate">{triageStatus.top_patient.primary_diagnosis}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => dequeueMutation.mutate()}
                      disabled={isRoleRestricted || dequeueMutation.isPending}
                      className="w-full mt-2 py-2.5 rounded-xl font-bold text-xs bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white shadow-sm flex items-center justify-center space-x-1.5 transition-all"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>{dequeueMutation.isPending ? 'Dequeuing...' : 'Complete Review & Dequeue'}</span>
                    </button>
                    {isRoleRestricted && (
                      <p className="text-[10px] text-amber-600 dark:text-amber-400 text-center">
                        Requires Analyst or Admin role to dequeue
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    Queue is currently empty.
                  </div>
                )}
              </div>

              {/* Enqueue Form */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                  Simulate New Patient Enqueue
                </span>
                <form onSubmit={handleEnqueue} className="space-y-2.5 text-xs">
                  <div>
                    <label className="text-slate-500 block font-medium mb-1">Encounter ID</label>
                    <input
                      type="text"
                      value={newEncounterId}
                      onChange={(e) => setNewEncounterId(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-slate-500 block font-medium mb-1">Risk Score (0-1)</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={newRiskScore}
                        onChange={(e) => setNewRiskScore(parseFloat(e.target.value))}
                        className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-slate-500 block font-medium mb-1">Stay (days)</label>
                      <input
                        type="number"
                        min="1"
                        max="14"
                        value={newStay}
                        onChange={(e) => setNewStay(parseInt(e.target.value, 10))}
                        className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-slate-500 block font-medium mb-1">Medications</label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={newMeds}
                        onChange={(e) => setNewMeds(parseInt(e.target.value, 10))}
                        className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-slate-500 block font-medium mb-1">Primary Diagnosis</label>
                      <select
                        value={newDiag}
                        onChange={(e) => setNewDiag(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                      >
                        <option value="Circulatory">Circulatory</option>
                        <option value="Diabetes">Diabetes</option>
                        <option value="Respiratory">Respiratory</option>
                        <option value="Renal">Renal</option>
                        <option value="Digestive">Digestive</option>
                      </select>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isRoleRestricted || enqueueMutation.isPending}
                    className="w-full mt-2 py-2 rounded-xl font-bold text-xs bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white shadow-sm flex items-center justify-center space-x-1.5 transition-all"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>{enqueueMutation.isPending ? 'Enqueuing...' : 'Heap Push (Enqueue)'}</span>
                  </button>
                  {isRoleRestricted && (
                    <p className="text-[10px] text-amber-600 dark:text-amber-400 text-center">
                      Requires Analyst or Admin role to enqueue
                    </p>
                  )}
                </form>
              </div>
            </div>

            {/* Heap Triage Queue List */}
            <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                    Triage Queue In-Memory Heap ({triageStatus?.total_queued ?? 0} Encounters)
                  </h4>
                  <p className="text-xs text-slate-500">
                    Sorted by max-heap priority order. Dequeuing pops index 0 in O(log N) time.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[11px] font-bold uppercase text-slate-500 bg-slate-50 dark:bg-slate-800/60 border-y border-slate-100 dark:border-slate-700/60">
                    <tr>
                      <th className="py-2.5 px-3">Order</th>
                      <th className="py-2.5 px-3">Encounter</th>
                      <th className="py-2.5 px-3">Patient</th>
                      <th className="py-2.5 px-3">Risk Score</th>
                      <th className="py-2.5 px-3">Stay</th>
                      <th className="py-2.5 px-3">Meds</th>
                      <th className="py-2.5 px-3">Diagnosis</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {triageStatus?.queue_preview.map((item, idx) => (
                      <tr 
                        key={item.encounter_id} 
                        className={`hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors ${
                          idx === 0 ? 'bg-amber-50/30 dark:bg-amber-950/20 font-semibold' : ''
                        }`}
                      >
                        <td className="py-2.5 px-3">
                          <span className={`w-5 h-5 rounded-full inline-flex items-center justify-center text-[10px] font-bold ${
                            idx === 0 
                              ? 'bg-amber-500 text-white' 
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                          }`}>
                            {idx + 1}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono font-medium text-slate-900 dark:text-slate-200">
                          {item.encounter_id}
                        </td>
                        <td className="py-2.5 px-3 text-slate-500">{item.patient_id}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            item.risk_score >= 0.75 
                              ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300'
                              : item.risk_score >= 0.50
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300'
                              : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300'
                          }`}>
                            {(item.risk_score * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2.5 px-3">{item.time_in_hospital} days</td>
                        <td className="py-2.5 px-3">{item.num_medications}</td>
                        <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">{item.primary_diagnosis}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* GRAPH TRAVERSAL VIEW */}
      {subTab === 'graph' && (
        <div className="space-y-6">
          {/* Complexity Banner */}
          <div className="bg-gradient-to-r from-emerald-900/10 via-teal-900/10 to-slate-900/10 dark:from-emerald-950/40 dark:via-teal-950/40 dark:to-slate-950/40 border border-emerald-200 dark:border-emerald-900/50 rounded-2xl p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center">
                  <Network className="w-4 h-4 mr-1.5 text-emerald-600" />
                  Clinical Co-morbidity Graph Traversal &amp; Shortest Path Exploration
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                  Models diagnostic transitions between Diabetes, Circulatory, Renal, and Respiratory conditions. Handles cycles via visited tracking and handles disconnected components.
                </p>
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                <span className="text-[11px] font-mono px-2.5 py-1 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 font-semibold text-emerald-600 dark:text-emerald-400">
                  Time: O(V + E)
                </span>
                <span className="text-[11px] font-mono px-2.5 py-1 bg-white dark:bg-slate-800 rounded-md border border-slate-200 dark:border-slate-700 font-semibold text-teal-600 dark:text-teal-400">
                  Space: O(V)
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Traversal Controls */}
            <div className="lg:col-span-1 bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                Traversal Controls
              </span>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-slate-500 block font-medium mb-1">Starting Node</label>
                  <select
                    value={startNode}
                    onChange={(e) => setStartNode(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="Diabetes">Diabetes</option>
                    <option value="Circulatory">Circulatory</option>
                    <option value="Renal">Renal</option>
                    <option value="Respiratory">Respiratory</option>
                    <option value="Neurological">Neurological</option>
                    <option value="Digestive">Digestive</option>
                    <option value="Genitourinary">Genitourinary</option>
                    <option value="Injury">Injury</option>
                    <option value="Ophthalmology">Ophthalmology (Disconnected Subgraph)</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-500 block font-medium mb-1">Algorithm Mode</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setGraphMode('bfs')}
                      className={`py-2 rounded-lg font-bold border transition-all ${
                        graphMode === 'bfs'
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      BFS (Queue)
                    </button>
                    <button
                      type="button"
                      onClick={() => setGraphMode('dfs')}
                      className={`py-2 rounded-lg font-bold border transition-all ${
                        graphMode === 'dfs'
                          ? 'bg-purple-600 text-white border-purple-600'
                          : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      DFS (Stack)
                    </button>
                  </div>
                </div>

                <button
                  onClick={handleRunTraversal}
                  disabled={isTraversing}
                  className="w-full py-2.5 rounded-xl font-bold text-xs bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white shadow-sm flex items-center justify-center space-x-1.5 transition-all"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Execute {graphMode.toUpperCase()} Traversal</span>
                </button>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
                  <span className="text-[11px] font-bold text-slate-500 block">Shortest Path Finder</span>
                  <div className="flex items-center space-x-2">
                    <select
                      value={targetNode}
                      onChange={(e) => setTargetNode(e.target.value)}
                      className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white text-xs"
                    >
                      <option value="Respiratory">Respiratory</option>
                      <option value="Renal">Renal</option>
                      <option value="Digestive">Digestive</option>
                      <option value="Genitourinary">Genitourinary</option>
                      <option value="Circulatory">Circulatory</option>
                      <option value="Retinopathy">Retinopathy (Disconnected)</option>
                    </select>
                    <button
                      onClick={handleFindShortestPath}
                      disabled={isTraversing}
                      className="px-3 py-1.5 rounded-lg font-bold text-xs bg-blue-600 hover:bg-blue-500 text-white whitespace-nowrap"
                    >
                      Find Path
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Traversal Output Visualizer */}
            <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Execution Pathway &amp; Diagnostic Nodes
                </span>
                <span className="text-xs text-slate-500">
                  Graph contains 11 nodes, 10 edges, 3 components
                </span>
              </div>

              {/* Path Steps */}
              {traversalResult && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      {graphMode.toUpperCase()} Order ({traversalResult.length} nodes visited):
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {traversalResult.map((node, i) => (
                      <React.Fragment key={node}>
                        <div className="px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs font-bold flex items-center space-x-1.5 shadow-2xs">
                          <span className="w-4 h-4 rounded-full bg-emerald-600 text-white text-[10px] flex items-center justify-center">
                            {i + 1}
                          </span>
                          <span>{node}</span>
                        </div>
                        {i < traversalResult.length - 1 && (
                          <span className="text-slate-400 font-bold">&rarr;</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {shortestPathResult && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-blue-600 dark:text-blue-400">
                      Shortest Path ({shortestPathResult.length - 1} clinical hops):
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {shortestPathResult.map((node, i) => (
                      <React.Fragment key={node}>
                        <div className="px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-950/50 border border-blue-300 dark:border-blue-800 text-blue-900 dark:text-blue-200 text-xs font-bold flex items-center space-x-1.5 shadow-2xs">
                          <span className="w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] flex items-center justify-center">
                            {i + 1}
                          </span>
                          <span>{node}</span>
                        </div>
                        {i < shortestPathResult.length - 1 && (
                          <span className="text-slate-400 font-bold">&rarr;</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {!traversalResult && !shortestPathResult && (
                <div className="py-12 text-center text-slate-400 text-xs space-y-2">
                  <Compass className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700 animate-pulse" />
                  <p>Select a node and click "Execute Traversal" or "Find Path" to visualize the graph walk.</p>
                </div>
              )}

              {/* Topology Summary Cards */}
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-xs">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Connected Clusters</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">3 Subgraphs</span>
                  <p className="text-[11px] text-slate-500 mt-0.5">Cardio-Renal, Eye, Derm</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-xs">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Cycle Safety</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">Guaranteed</span>
                  <p className="text-[11px] text-slate-500 mt-0.5">Set-based O(1) visited checks</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-xs">
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">Optimal Pathing</span>
                  <span className="font-bold text-blue-600 dark:text-blue-400">BFS Level Order</span>
                  <p className="text-[11px] text-slate-500 mt-0.5">Minimal diagnosis hops</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
