import React, { useState, useEffect, useRef } from 'react';
import { Shield, Server, Activity, Terminal } from 'lucide-react';

import ScanHistory from './components/ScanHistory';
import ScanProgress from './components/ScanProgress';
import Findings from './components/Findings';
import ReportView from './components/ReportView';
import ChatPanel from './components/ChatPanel';

import './App.css';

function App() {
  const [scans, setScans] = useState([]);
  const [currentScan, setCurrentScan] = useState(null);
  const [progressUpdates, setProgressUpdates] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const wsRef = useRef(null);

  // Fetch scan history on mount
  useEffect(() => {
    fetchScans();
  }, []);

  const fetchScans = async () => {
    try {
      const res = await fetch('/api/scans');
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      if (Array.isArray(data)) {
        setScans(data);
      } else {
        setScans([]);
      }
    } catch (err) {
      console.error("Failed to fetch scans:", err);
      setScans([]);
    }
  };

  const loadScan = async (scanId) => {
    try {
      const res = await fetch(`/api/scan/${scanId}`);
      const data = await res.json();
      setCurrentScan(data);
      setProgressUpdates([]);
      
      // Connect to WS if scan is running
      if (['pending', 'planning', 'executing', 'analyzing', 'reporting'].includes(data.status)) {
        connectWebSocket(scanId);
      } else {
        if (wsRef.current) wsRef.current.close();
      }

      // Fetch chat history
      try {
        const chatRes = await fetch(`/api/chat/${scanId}`);
        if (chatRes.ok) {
          const chatData = await chatRes.json();
          setChatHistory(chatData);
        } else {
          setChatHistory([]);
        }
      } catch (err) {
        setChatHistory([]);
      }
    } catch (err) {
      console.error("Failed to load scan:", err);
    }
  };

  const connectWebSocket = (scanId) => {
    if (wsRef.current) wsRef.current.close();

    const wsUrl = `ws://${window.location.host}/api/ws/${scanId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setProgressUpdates(prev => [...prev, update]);
      
      setCurrentScan(prev => {
        if (!prev) return prev;
        return { ...prev, status: update.status };
      });

      if (['completed', 'failed'].includes(update.status)) {
        // Refresh full scan data when done
        setTimeout(() => loadScan(scanId), 1000);
      }
    };

    wsRef.current = ws;
  };

  const handleNewScan = async (target, objective) => {
    try {
      const res = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, objective })
      });
      const data = await res.json();
      
      // Connect WebSocket FIRST before loadScan to avoid missing early events
      connectWebSocket(data.scan_id);

      // Add to list and select it
      const newScanEntry = { scan_id: data.scan_id, target, status: 'pending', created_at: new Date().toISOString() };
      setScans(prev => [newScanEntry, ...prev]);
      setCurrentScan({ scan_id: data.scan_id, target, objective, status: 'pending' });
      setProgressUpdates([]);
      setChatHistory([]);

    } catch (err) {
      console.error("Failed to start scan:", err);
    }
  };

  const handleDeleteScan = async (scanId) => {
    try {
      const res = await fetch(`/api/scan/${scanId}`, { method: 'DELETE' });
      if (res.ok) {
        setScans(scans.filter(s => s.scan_id !== scanId));
        if (currentScan?.scan_id === scanId) {
          setCurrentScan(null);
          setChatHistory([]);
          setProgressUpdates([]);
        }
      }
    } catch (err) {
      console.error("Failed to delete scan:", err);
    }
  };

  const handleSendMessage = async (message) => {
    if (!currentScan) return;

    // Add user message immediately
    const newUserMsg = { role: 'user', content: message };
    setChatHistory(prev => [...prev, newUserMsg]);
    setIsChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, scan_id: currentScan.scan_id })
      });
      const data = await res.json();
      
      setChatHistory(prev => [...prev, data]);
    } catch (err) {
      console.error("Chat failed:", err);
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error processing your request.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Determine what to show in center panel
  const isRunning = currentScan && ['pending', 'planning', 'executing', 'analyzing', 'reporting'].includes(currentScan.status);
  const isCompleted = currentScan && currentScan.status === 'completed';
  const hasFindings = currentScan?.analysis?.findings?.length > 0;

  return (
    <div className="app-container" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header className="app-header">
        <div className="app-logo">
          <div className="app-logo-icon">
            <Shield size={20} color="#fff" />
          </div>
          <div>
            <h1>Argus AI</h1>
            <span>Reconnaissance Platform</span>
          </div>
        </div>
        <div className="header-actions">
          <div className="header-status">
            <div className="status-dot"></div>
            System Online
          </div>
        </div>
      </header>

      <main className="app-main">
        {/* Left Panel: History */}
        <ScanHistory 
          scans={scans} 
          currentScanId={currentScan?.scan_id}
          onSelectScan={loadScan}
          onNewScan={handleNewScan}
          onDeleteScan={handleDeleteScan}
        />

        {/* Center Panel: Main View */}
        <div className="panel center-panel">
          <div className="panel-header">
            <h2>{currentScan ? `Dashboard: ${currentScan.target}` : 'Dashboard'}</h2>
          </div>
          <div className="panel-content">
            {!currentScan ? (
              <div className="welcome-state animate-slide-up">
                <Shield className="welcome-icon text-cyan-500" />
                <h2>Welcome to Argus AI</h2>
                <p>Start a new reconnaissance scan from the sidebar to automatically map attack surfaces, detect technologies, and identify vulnerabilities.</p>
              </div>
            ) : (
              <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                
                {/* Always show progress if running or if we have progress updates */}
                {(isRunning || progressUpdates.length > 0) && (
                  <ScanProgress 
                    status={currentScan.status} 
                    progressUpdates={progressUpdates} 
                  />
                )}

                {/* Show Findings if completed or if we have analysis data */}
                {(isCompleted || currentScan.analysis?.summary) && (
                  <Findings analysis={currentScan.analysis} />
                )}

                {/* Show Report if completed */}
                {isCompleted && currentScan.report?.executive_summary && (
                  <ReportView report={currentScan.report} />
                )}

                {/* Show Failed state */}
                {currentScan.status === 'failed' && (
                  <div className="welcome-state animate-slide-up" style={{marginTop: '40px'}}>
                    <Shield className="welcome-icon text-red-500" style={{color: '#ef4444'}} />
                    <h2 style={{color: '#ef4444'}}>Scan Failed</h2>
                    <p>The reconnaissance process encountered an error.</p>
                    <button 
                      className="btn btn-primary"
                      onClick={() => handleNewScan(currentScan.target, currentScan.objective)}
                      style={{marginTop: '16px'}}
                    >
                      Restart Scan
                    </button>
                  </div>
                )}

              </div>
            )}
          </div>
        </div>

        {/* Right Panel: AI Chat */}
        <ChatPanel 
          scanId={currentScan?.scan_id}
          chatHistory={chatHistory}
          onSendMessage={handleSendMessage}
          isChatLoading={isChatLoading}
        />
      </main>
    </div>
  );
}

export default App;
