import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Download } from 'lucide-react';

export default function ReportView({ report }) {
  const [activeTab, setActiveTab] = useState('executive');

  if (!report) return null;

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([report.full_markdown || "# Security Report"], {type: 'text/markdown'});
    element.href = URL.createObjectURL(file);
    element.download = `recon-report-${report.target}-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(element); // Required for this to work in FireFox
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="report-section animate-slide-up">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={18} className="text-blue-400" /> Final Report
        </h3>
        {report.full_markdown && (
          <button className="btn btn-secondary btn-sm" onClick={handleDownload}>
            <Download size={14} /> Export Markdown
          </button>
        )}
      </div>

      <div className="report-tabs">
        <button 
          className={`report-tab ${activeTab === 'executive' ? 'active' : ''}`}
          onClick={() => setActiveTab('executive')}
        >
          Executive Summary
        </button>
        <button 
          className={`report-tab ${activeTab === 'technical' ? 'active' : ''}`}
          onClick={() => setActiveTab('technical')}
        >
          Technical Details
        </button>
        {report.full_markdown && (
          <button 
            className={`report-tab ${activeTab === 'full' ? 'active' : ''}`}
            onClick={() => setActiveTab('full')}
          >
            Full Markdown
          </button>
        )}
      </div>

      <div className="report-content">
        {activeTab === 'executive' && (
          <div>
            <h2 style={{ marginTop: 0 }}>Executive Summary</h2>
            <ReactMarkdown>{report.executive_summary}</ReactMarkdown>
            
            <h3 style={{ marginTop: '24px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>Key Metrics</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li><strong>Target:</strong> {report.target}</li>
              <li><strong>Date:</strong> {new Date(report.scan_date || Date.now()).toLocaleDateString()}</li>
              <li><strong>Assets Discovered:</strong> {report.assets_discovered?.length || 0}</li>
              <li><strong>Critical/High Vulnerabilities:</strong> {
                (report.vulnerabilities || []).filter(v => v.severity === 'critical' || v.severity === 'high').length
              }</li>
            </ul>

            {report.recommendations && report.recommendations.length > 0 && (
              <>
                <h3 style={{ marginTop: '24px', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>Primary Recommendations</h3>
                <ul>
                  {report.recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {activeTab === 'technical' && (
          <div>
            <h2 style={{ marginTop: 0 }}>Technical Summary</h2>
            <ReactMarkdown>{report.technical_summary}</ReactMarkdown>
          </div>
        )}

        {activeTab === 'full' && report.full_markdown && (
          <div>
            <ReactMarkdown>{report.full_markdown}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
