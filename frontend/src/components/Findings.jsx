import React, { useState } from 'react';
import { Shield, Server, Globe, Cpu, AlertTriangle, Download, X, FileText, Code } from 'lucide-react';

export default function Findings({ analysis }) {
  if (!analysis) return null;

  const {
    summary,
    total_assets_found = 0,
    unique_subdomains = [],
    live_hosts = [],
    technologies = [],
    findings = [],
    next_steps = []
  } = analysis;

  const getSeverityBadge = (severity) => {
    return <span className={`badge badge-${severity}`}>{severity}</span>;
  };

  const [modalState, setModalState] = useState({ isOpen: false, title: '', data: [] });

  const triggerDownload = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadJSON = (data, title) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    triggerDownload(blob, `${title.toLowerCase().replace(/\s+/g, '_')}.json`);
  };

  const downloadCSV = (data, title) => {
    let csvContent = "";
    if (data.length > 0 && typeof data[0] === 'object') {
      const headers = Object.keys(data[0]).join(',');
      const rows = data.map(obj => Object.values(obj).map(v => `"${String(typeof v === 'object' ? JSON.stringify(v) : v).replace(/"/g, '""')}"`).join(',')).join('\n');
      csvContent = `${headers}\n${rows}`;
    } else {
      csvContent = data.join('\n');
    }
    const blob = new Blob([csvContent], { type: 'text/csv' });
    triggerDownload(blob, `${title.toLowerCase().replace(/\s+/g, '_')}.csv`);
  };

  const downloadTXT = (data, title) => {
    const content = typeof data[0] === 'object' ? JSON.stringify(data, null, 2) : data.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    triggerDownload(blob, `${title.toLowerCase().replace(/\s+/g, '_')}.txt`);
  };

  const openModal = (title, data) => {
    if (data && data.length > 0) {
      setModalState({ isOpen: true, title, data });
    }
  };

  return (
    <div className="findings-section animate-slide-up">
      <h3>Analysis Overview</h3>
      
      {summary && (
        <div style={{ marginBottom: '24px', color: '#94a3b8', lineHeight: '1.6' }}>
          {summary}
        </div>
      )}

      <div className="stats-row">
        <div className="stat-card" style={{cursor: 'pointer'}} onClick={() => openModal('Subdomains', unique_subdomains)}>
          <Globe className="text-cyan-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{unique_subdomains.length}</div>
          <div className="stat-label">Subdomains</div>
        </div>
        <div className="stat-card" style={{cursor: 'pointer'}} onClick={() => openModal('Live Hosts', live_hosts)}>
          <Server className="text-emerald-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{live_hosts.length}</div>
          <div className="stat-label">Live Hosts</div>
        </div>
        <div className="stat-card" style={{cursor: 'pointer'}} onClick={() => openModal('Tech Stack', technologies)}>
          <Cpu className="text-purple-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{technologies.length}</div>
          <div className="stat-label">Tech Stack</div>
        </div>
        <div className="stat-card" style={{cursor: 'pointer'}} onClick={() => openModal('Findings', findings)}>
          <Shield className="text-orange-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{findings.length}</div>
          <div className="stat-label">Findings</div>
        </div>
      </div>

      {unique_subdomains.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '8px', color: '#cbd5e1' }}>Discovered Subdomains</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', maxHeight: '200px', overflowY: 'auto', padding: '4px' }}>
            {unique_subdomains.map((sub, i) => (
              <span key={i} className="asset-tag" style={{ background: 'rgba(6, 182, 212, 0.1)', borderColor: 'rgba(6, 182, 212, 0.3)', color: '#22d3ee' }}>
                {sub}
              </span>
            ))}
          </div>
        </div>
      )}

      {technologies.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '8px', color: '#cbd5e1' }}>Detected Technologies</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {technologies.map((tech, i) => (
              <span key={i} className="asset-tag" style={{ background: 'rgba(124, 58, 237, 0.1)', borderColor: 'rgba(124, 58, 237, 0.3)', color: '#a78bfa' }}>
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {findings.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.9rem', marginBottom: '12px', color: '#cbd5e1' }}>Key Findings</h4>
          <div className="findings-grid">
            {findings.map((finding, idx) => (
              <div key={idx} className="finding-card">
                <div className="finding-card-header">
                  <div className="finding-card-title">{finding.title}</div>
                  {getSeverityBadge(finding.severity)}
                </div>
                <div className="finding-card-description">
                  {finding.description}
                </div>
                {finding.affected_assets && finding.affected_assets.length > 0 && (
                  <div className="finding-card-assets">
                    {finding.affected_assets.map((asset, i) => (
                      <span key={i} className="asset-tag">{asset}</span>
                    ))}
                  </div>
                )}
                {finding.related_cves && finding.related_cves.length > 0 && (
                  <div style={{ marginTop: '10px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {finding.related_cves.map((cve, i) => (
                      <span key={i} className="badge" style={{ background: 'rgba(220, 38, 38, 0.1)', color: '#fca5a5', border: '1px solid rgba(220, 38, 38, 0.3)' }}>
                        {cve}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {next_steps && next_steps.length > 0 && (
        <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(245, 158, 11, 0.05)', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: '#fbbf24', marginBottom: '12px' }}>
            <AlertTriangle size={16} /> Recommended Next Steps
          </h4>
          <ul style={{ paddingLeft: '24px', color: '#d1d5db', fontSize: '0.9rem' }}>
            {next_steps.map((step, i) => (
              <li key={i} style={{ marginBottom: '6px' }}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      {modalState.isOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div style={{ background: '#1e293b', padding: '24px', borderRadius: '12px', width: '100%', maxWidth: '800px', maxHeight: '90vh', display: 'flex', flexDirection: 'column', border: '1px solid #334155', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '1.2rem' }}>{modalState.title} ({modalState.data.length})</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setModalState({ isOpen: false, title: '', data: [] })}>
                <X size={20} />
              </button>
            </div>
            
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <button className="btn btn-ghost btn-sm" onClick={() => downloadJSON(modalState.data, modalState.title)} style={{ border: '1px solid #334155', color: '#cbd5e1' }}>
                <Code size={14} /> Download JSON
              </button>
              <button className="btn btn-ghost btn-sm" onClick={() => downloadCSV(modalState.data, modalState.title)} style={{ border: '1px solid #334155', color: '#cbd5e1' }}>
                <FileText size={14} /> Download CSV
              </button>
              <button className="btn btn-ghost btn-sm" onClick={() => downloadTXT(modalState.data, modalState.title)} style={{ border: '1px solid #334155', color: '#cbd5e1' }}>
                <Download size={14} /> Download TXT
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', background: '#0f172a', padding: '16px', borderRadius: '8px', border: '1px solid #334155' }}>
              {modalState.data.length > 0 && typeof modalState.data[0] === 'object' ? (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left' }}>
                        {Object.keys(modalState.data[0]).map(k => <th key={k} style={{ padding: '10px 8px', color: '#94a3b8', fontWeight: 600 }}>{k.replace(/_/g, ' ').toUpperCase()}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {modalState.data.map((row, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                          {Object.values(row).map((val, j) => <td key={j} style={{ padding: '10px 8px', color: '#cbd5e1' }}>{typeof val === 'object' ? JSON.stringify(val) : String(val)}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <ul style={{ margin: 0, paddingLeft: '20px', color: '#cbd5e1', fontSize: '0.9rem', listStyleType: 'disc' }}>
                  {modalState.data.map((item, i) => <li key={i} style={{ padding: '6px 0', wordBreak: 'break-all' }}>{item}</li>)}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
