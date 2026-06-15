import React, { useState } from 'react';
import { Search, Plus, Shield, ShieldAlert, CheckCircle, Clock, AlertCircle, Activity, Trash2 } from 'lucide-react';

export default function ScanHistory({ scans, currentScanId, onSelectScan, onNewScan, onDeleteScan }) {
  const [target, setTarget] = useState('');
  const [objective, setObjective] = useState('');
  const [isFormOpen, setIsFormOpen] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (target) {
      onNewScan(target, objective || 'Perform a complete attack surface assessment');
      setTarget('');
      setObjective('');
      setIsFormOpen(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle size={14} className="text-emerald-500" />;
      case 'failed': return <AlertCircle size={14} className="text-red-500" />;
      case 'executing':
      case 'planning':
      case 'analyzing':
      case 'reporting':
        return <Activity size={14} className="text-cyan-500 animate-pulse" />;
      default: return <Clock size={14} className="text-gray-400" />;
    }
  };

  return (
    <div className="panel scan-history-panel">
      <div className="panel-header">
        <h2>Scan History</h2>
        <button 
          className="btn btn-ghost btn-sm"
          onClick={() => setIsFormOpen(!isFormOpen)}
          title="New Scan"
        >
          <Plus size={16} />
        </button>
      </div>

      {isFormOpen && (
        <form onSubmit={handleSubmit} className="new-scan-form animate-slide-up">
          <input
            type="text"
            className="input"
            placeholder="Target (e.g. example.com)"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            required
          />
          <textarea
            className="input"
            placeholder="Objective (Optional)"
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            rows={2}
            style={{ resize: 'none', marginBottom: '8px' }}
          />
          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
            <Search size={16} /> Start Scan
          </button>
        </form>
      )}

      <div className="panel-content" style={{ padding: '12px' }}>
        {!Array.isArray(scans) || scans.length === 0 ? (
          <div className="empty-state">
            <Shield className="empty-state-icon" />
            <h4>No scans yet</h4>
            <p>Start a new scan to see history here.</p>
          </div>
        ) : (
          scans.map((scan) => (
            <div 
              key={scan.scan_id} 
              className={`scan-item ${currentScanId === scan.scan_id ? 'active' : ''}`}
              onClick={() => onSelectScan(scan.scan_id)}
            >
              <div className="scan-item-target" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{scan.target}</span>
                <button 
                  className="btn btn-ghost btn-sm" 
                  style={{ padding: '4px', opacity: 0.6 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    if(window.confirm('Are you sure you want to delete this scan?')) {
                      onDeleteScan(scan.scan_id);
                    }
                  }}
                  title="Delete Scan"
                >
                  <Trash2 size={14} className="text-red-500" />
                </button>
              </div>
              <div className="scan-item-meta">
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {getStatusIcon(scan.status)}
                  <span className="scan-item-date">
                    {scan.created_at ? new Date(scan.created_at).toLocaleDateString() : 'Just now'}
                  </span>
                </div>
                {scan.total_findings > 0 && (
                  <span className="scan-item-findings" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldAlert size={12} className="text-orange-500" />
                    {scan.total_findings} findings
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}


