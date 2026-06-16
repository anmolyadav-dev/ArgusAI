import React from 'react';
import { Shield, Server, Globe, Cpu, AlertTriangle } from 'lucide-react';

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

  return (
    <div className="findings-section animate-slide-up">
      <h3>Analysis Overview</h3>
      
      {summary && (
        <div style={{ marginBottom: '24px', color: '#94a3b8', lineHeight: '1.6' }}>
          {summary}
        </div>
      )}

      <div className="stats-row">
        <div className="stat-card">
          <Globe className="text-cyan-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{unique_subdomains.length}</div>
          <div className="stat-label">Subdomains</div>
        </div>
        <div className="stat-card">
          <Server className="text-emerald-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{live_hosts.length}</div>
          <div className="stat-label">Live Hosts</div>
        </div>
        <div className="stat-card">
          <Cpu className="text-purple-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{technologies.length}</div>
          <div className="stat-label">Tech Stack</div>
        </div>
        <div className="stat-card">
          <Shield className="text-orange-500 mx-auto mb-2" size={24} />
          <div className="stat-value">{findings.length}</div>
          <div className="stat-label">Findings</div>
        </div>
      </div>

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
    </div>
  );
}
