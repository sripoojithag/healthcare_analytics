import React from 'react';
import { Shield, ShieldAlert, CheckCircle2, XCircle, Clock, Key } from 'lucide-react';

interface AuditTrailPanelProps {
  currentRole: string;
}

export const AuditTrailPanel: React.FC<AuditTrailPanelProps> = ({ currentRole }) => {
  if (currentRole !== "admin") {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-500 flex items-center justify-center mx-auto">
          <Key className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Security Audit Trail Restricted (Admin Only)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
            Audit logging records authentication, role authorizations, and data access. Reviewing the security audit log is restricted strictly to the <strong>Admin</strong> role.
          </p>
        </div>
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
          <Shield className="w-3.5 h-3.5" />
          <span>Switch role to Admin above to inspect audit logs</span>
        </div>
      </div>
    );
  }

  // Sample audit events matching real security logs
  const logs = [
    { timestamp: "2026-11-05T09:28:05Z", user: "admin_service", role: "admin", action: "AUTHORIZE", resource: "/api/v1/audit/logs", status: "SUCCESS" },
    { timestamp: "2026-11-05T09:28:03Z", user: "viewer_user", role: "viewer", action: "AUTHORIZE", resource: "/api/v1/audit/logs", status: "DENIED" },
    { timestamp: "2026-11-05T09:27:58Z", user: "admin_user", role: "admin", action: "AUTHORIZE", resource: "/api/v1/ingestion/upload", status: "SUCCESS" },
    { timestamp: "2026-11-05T09:27:55Z", user: "analyst_user", role: "analyst", action: "AUTHORIZE", resource: "/api/v1/ingestion/upload", status: "DENIED" },
    { timestamp: "2026-11-05T09:27:50Z", user: "analyst_user", role: "analyst", action: "AUTHORIZE", resource: "/api/v1/encounters", status: "SUCCESS" },
    { timestamp: "2026-11-05T09:27:45Z", user: "viewer_user", role: "viewer", action: "AUTHORIZE", resource: "/api/v1/encounters", status: "DENIED" }
  ];

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 sm:p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span>Security &amp; Governance Audit Trail</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Immutable log of role evaluations and resource authorizations (HIPAA-aligned: zero PHI logged)
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
          Admin Audit Stream
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs font-mono">
          <thead className="bg-slate-50 dark:bg-slate-800/60 font-semibold text-slate-700 dark:text-slate-300">
            <tr>
              <th className="px-3 py-2 text-left">Timestamp (UTC)</th>
              <th className="px-3 py-2 text-left">Actor / User</th>
              <th className="px-3 py-2 text-left">Assigned Role</th>
              <th className="px-3 py-2 text-left">Action</th>
              <th className="px-3 py-2 text-left">Resource Endpoint</th>
              <th className="px-3 py-2 text-right">Access Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400">
            {logs.map((log, idx) => (
              <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                <td className="px-3 py-2 whitespace-nowrap text-slate-400">{log.timestamp}</td>
                <td className="px-3 py-2 whitespace-nowrap font-bold text-slate-800 dark:text-slate-200">{log.user}</td>
                <td className="px-3 py-2 whitespace-nowrap">
                  <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {log.role}
                  </span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-blue-600 dark:text-blue-400 font-semibold">{log.action}</td>
                <td className="px-3 py-2 whitespace-nowrap">{log.resource}</td>
                <td className="px-3 py-2 whitespace-nowrap text-right">
                  {log.status === "SUCCESS" ? (
                    <span className="inline-flex items-center text-emerald-600 dark:text-emerald-400 font-bold text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> ALLOWED
                    </span>
                  ) : (
                    <span className="inline-flex items-center text-rose-600 dark:text-rose-400 font-bold text-[11px]">
                      <XCircle className="w-3.5 h-3.5 mr-1" /> FORBIDDEN
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
