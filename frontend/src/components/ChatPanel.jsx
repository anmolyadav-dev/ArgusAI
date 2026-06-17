import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, MessageSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function ChatPanel({ scanId, chatHistory = [], onSendMessage, isChatLoading }) {
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, isChatLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isChatLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const suggestions = [
    "Summarize the findings",
    "What are the critical vulnerabilities?",
    "Explain the detected technologies",
    "What should I investigate first?"
  ];

  return (
    <div className="panel chat-panel">
      <div className="panel-header">
        <h2>AI Assistant</h2>
        <MessageSquare size={16} className="text-cyan-500" />
      </div>

      <div className="chat-messages">
        {chatHistory.length === 0 ? (
          <div className="empty-state" style={{ padding: '20px' }}>
            <Bot className="empty-state-icon text-cyan-500" />
            <h4 style={{ color: '#e2e8f0' }}>Ready to analyze</h4>
            <p style={{ fontSize: '0.8rem' }}>Ask me about the scan results, vulnerabilities, or recommendations.</p>
          </div>
        ) : (
          chatHistory.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.role}`}>
              <div className="chat-avatar">
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className="chat-bubble">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown 
                    components={{
                      p: ({node, ...props}) => <p style={{margin: '0 0 8px 0'}} {...props} />,
                      ul: ({node, ...props}) => <ul style={{margin: '4px 0', paddingLeft: '20px'}} {...props} />,
                      ol: ({node, ...props}) => <ol style={{margin: '4px 0', paddingLeft: '20px'}} {...props} />,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))
        )}
        
        {isChatLoading && (
          <div className="chat-message assistant">
            <div className="chat-avatar"><Bot size={16} /></div>
            <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div className="spinner spinner-sm"></div> Thinking...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {scanId && chatHistory.length === 0 && (
        <div className="chat-suggestions">
          {suggestions.map((suggestion, idx) => (
            <div 
              key={idx} 
              className="chat-suggestion"
              onClick={() => onSendMessage(suggestion)}
            >
              {suggestion}
            </div>
          ))}
        </div>
      )}

      <form className="chat-input-area" onSubmit={handleSubmit}>
        <input
          type="text"
          className="input"
          placeholder="Ask a question..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={!scanId || isChatLoading}
        />
        <button 
          type="submit" 
          className="btn btn-primary" 
          style={{ padding: '10px' }}
          disabled={!scanId || !message.trim() || isChatLoading}
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
