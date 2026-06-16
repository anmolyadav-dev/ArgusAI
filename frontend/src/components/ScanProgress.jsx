import React, { useEffect, useRef } from 'react';
import { Activity, Terminal } from 'lucide-react';

export default function ScanProgress({ status, progressUpdates = [] }) {
  const logsEndRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom of logs
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [progressUpdates]);

  const getStatusText = () => {
    switch(status) {
      case 'pending': return 'Initializing scan...';
      case 'planning': return 'AI Planner is designing reconnaissance strategy...';
      case 'executing': return 'Execution Engine is running tools...';
      case 'analyzing': return 'AI Analyst is correlating findings...';
      case 'reporting': return 'AI Reporter is generating final report...';
      case 'completed': return 'Scan completed successfully.';
      case 'failed': return 'Scan failed.';
      default: return 'Waiting...';
    }
  };

  // Default to 0 if not set, or get the latest progress percent
  const latestPercent = progressUpdates.length > 0 
    ? progressUpdates[progressUpdates.length - 1].progress_percent 
    : 0;

  return (
    <div className="scan-progress-section">
      <div className="scan-progress-header">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} className="text-cyan-500 animate-pulse-glow" /> 
          Live Progress: <span className="text-cyan-400">{getStatusText()}</span>
        </h3>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {(status !== 'completed' && status !== 'failed' && status !== 'pending') && (
            <span style={{ fontWeight: 'bold', color: '#00d4ff' }}>{latestPercent}%</span>
          )}
          <span className={`badge badge-${status || 'pending'}`}>
            {status ? status.toUpperCase() : 'PENDING'}
          </span>
        </div>
      </div>

      {(status !== 'completed' && status !== 'failed' && status !== 'pending') && (
        <div className="progress-bar" style={{ marginBottom: '16px' }}>
          <div 
            className="progress-bar-fill" 
            style={{ width: `${latestPercent}%` }}
          />
        </div>
      )}

      {progressUpdates.length > 0 && (
        <div className="progress-logs">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#94a3b8', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
            <Terminal size={14} /> Execution Logs
          </div>
          {progressUpdates.map((update, idx) => (
            <div key={idx} className="progress-log-entry">
              <span className="log-time">
                {new Date(update.timestamp || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
              </span>
              <span className="log-stage">[{update.stage || update.status}]</span>
              <span className="log-message">
                {update.tool ? <span className="text-purple-400">[{update.tool}] </span> : ''}
                {update.message}
              </span>
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      )}
    </div>
  );
}
