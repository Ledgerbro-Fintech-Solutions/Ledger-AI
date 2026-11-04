import React, { useState, useRef, useEffect } from 'react';

const SUGGESTED_PROMPTS = [
  'What is the total expenditure across all invoices?',
  'Show me a bar chart of spending by vendor',
  'Which vendor has the highest billing amount?',
  'List all line items with quantity and unit price as a table',
  'Provide a breakdown of tax amounts and due dates'
];

const INITIAL_SAMPLE_DATA = [
  {
    invoice_number: 'INV-2026-0842',
    vendor_name: 'Dell Technologies',
    invoice_date: '2026-08-14',
    due_date: '2026-09-14',
    total_amount: 2450.00,
    currency: '$',
    items: [
      { description: 'Precision Workstation RAM Upgrade', quantity: 2, unit_price: 650.00, total_price: 1300.00 },
      { description: 'UltraSharp 32 4K Monitor', quantity: 1, unit_price: 1150.00, total_price: 1150.00 }
    ]
  },
  {
    invoice_number: 'INV-2026-0841',
    vendor_name: 'ABC Technologies',
    invoice_date: '2026-08-14',
    due_date: '2026-09-01',
    total_amount: 12890.50,
    currency: '$',
    items: [
      { description: 'Enterprise Server Maintenance Annual', quantity: 1, unit_price: 12890.50, total_price: 12890.50 }
    ]
  },
  {
    invoice_number: 'XYZ-992-B',
    vendor_name: 'XYZ Manufacturing',
    invoice_date: '2026-08-13',
    due_date: '2026-08-28',
    total_amount: 4200.00,
    currency: '$',
    items: [
      { description: 'CNC Custom Aluminum Brackets', quantity: 84, unit_price: 50.00, total_price: 4200.00 }
    ]
  },
  {
    invoice_number: 'PRM-00192',
    vendor_name: 'Prime Components',
    invoice_date: '2026-08-13',
    due_date: '2026-09-15',
    total_amount: 850.25,
    currency: '$',
    items: [
      { description: 'Shielded Copper Cabling 500m', quantity: 1, unit_price: 550.00, total_price: 550.00 },
      { description: 'RJ45 Termination Kits', quantity: 5, unit_price: 60.05, total_price: 300.25 }
    ]
  }
];

export default function ChatbotTab({ externalInvoiceData, onNavigateTab: _onNavigateTab }) {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: 'Hello! I am your Ledger AI Financial Assistant. Upload invoice documents or initialize your session to analyze spend, cross-examine vendors, or generate visual charts.',
      timestamp: 'Just now'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [activeFilesCount, setActiveFilesCount] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const msgCounter = useRef(100);

  // Index JSON data to start session
  const handleIndexJson = async (dataToUpload, filename = 'Invoices_Export.json') => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const response = await fetch('/api/v1/upload/json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: filename,
          data: dataToUpload
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || 'Failed to initialize session');
      }

      const res = await response.json();
      setSessionId(res.session_id);
      setActiveFilesCount(res.files_processed || 1);

      msgCounter.current += 1;
      setMessages((prev) => [
        ...prev,
        {
          id: msgCounter.current,
          sender: 'assistant',
          text: `Invoice dataset loaded successfully (${res.files_processed || 1} file indexed into Groq FAISS Vector Store). You can now ask questions about totals, items, vendors, or request graphs!`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  // If external invoice data was passed from Invoices tab
  useEffect(() => {
    if (externalInvoiceData && !sessionId) {
      handleIndexJson(externalInvoiceData, 'Dashboard_Invoices.json');
    }
  }, [externalInvoiceData, sessionId]);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Upload file from input
  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadError(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const response = await fetch('/api/v1/upload/files', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || 'Upload failed');
      }

      const res = await response.json();
      setSessionId(res.session_id);
      setActiveFilesCount(res.files_processed);

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          sender: 'assistant',
          text: `Indexed ${res.files_processed} document(s) into session. Session ID: ${res.session_id.slice(0, 8)}... Ask me anything!`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Send question
  const handleSendMessage = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    // Check if session exists; if not, initialize with default dataset
    let currentSession = sessionId;
    if (!currentSession) {
      setIsUploading(true);
      try {
        const initResp = await fetch('/api/v1/upload/json', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: 'workspace_invoices_sample.json',
            data: INITIAL_SAMPLE_DATA
          })
        });
        if (initResp.ok) {
          const initRes = await initResp.json();
          currentSession = initRes.session_id;
          setSessionId(currentSession);
          setActiveFilesCount(1);
        }
      } catch (e) {
        console.error('Session init error:', e);
      } finally {
        setIsUploading(false);
      }
    }

    if (!currentSession) {
      setUploadError('Please index documents or upload a file first.');
      return;
    }

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSession,
          question: query
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || errData.error || 'Analysis failed');
      }

      const res = await response.json();
      const botMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: res.answer,
        table: res.table,
        graph: res.graph,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: `Apologies, I encountered an error analyzing your question: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Reset chat
  const handleClearChat = () => {
    setMessages([
      {
        id: Date.now(),
        sender: 'assistant',
        text: 'Chat history cleared. You can continue asking questions about your indexed documents.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#F9F9FB]">
      
      {/* Top Header Bar */}
      <header className="h-16 border-b border-border-subtle bg-white flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
            <span className="material-symbols-outlined text-[20px]">smart_toy</span>
          </div>
          <div>
            <h1 className="font-sans text-base font-semibold text-text-primary flex items-center gap-2">
              Financial Intelligence Assistant
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Groq LLaMA / Qwen RAG
              </span>
            </h1>
            <p className="font-sans text-[11px] text-text-secondary">
              Natural language queries, tabular extraction, and Matplotlib visualizations powered by LangGraph
            </p>
          </div>
        </div>

        {/* Right Session Status & Action Controls */}
        <div className="flex items-center gap-2">
          {sessionId ? (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-soft border border-border-subtle text-xs text-text-secondary">
              <span className="material-symbols-outlined text-[16px] text-emerald-600">database</span>
              <span>Session: <strong className="text-text-primary">{sessionId.slice(0, 8)}...</strong></span>
              <span className="text-border-strong">•</span>
              <span>{activeFilesCount} file(s) indexed</span>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => handleIndexJson(INITIAL_SAMPLE_DATA, 'Default_Ledger_Data.json')}
              disabled={isUploading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-surface-soft hover:bg-surface-muted text-text-primary border border-border-subtle transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-blue-600">sync</span>
              {isUploading ? 'Indexing...' : 'Index Sample Data'}
            </button>
          )}

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv,.json"
            multiple
            className="hidden"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-surface-soft text-text-primary border border-border-subtle transition-colors shadow-2xs"
            title="Upload CSV or JSON invoices into vector store"
          >
            <span className="material-symbols-outlined text-[16px]">upload_file</span>
            {isUploading ? 'Uploading...' : 'Upload File'}
          </button>

          <button
            type="button"
            onClick={handleClearChat}
            className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-soft rounded-lg transition-colors"
            title="Clear Chat"
          >
            <span className="material-symbols-outlined text-[18px]">restart_alt</span>
          </button>
        </div>
      </header>

      {/* Upload Error Banner */}
      {uploadError && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2.5 flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-red-500">error</span>
            <span>{uploadError}</span>
          </div>
          <button onClick={() => setUploadError(null)} className="text-red-500 hover:text-red-800">
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      )}

      {/* Main Chat Stream Container */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div className="flex items-center gap-2 mb-1 px-1">
              <span className="font-sans text-[11px] font-medium text-text-secondary">
                {msg.sender === 'user' ? 'You' : 'Ledger AI'}
              </span>
              <span className="text-[10px] text-text-tertiary">{msg.timestamp}</span>
            </div>

            <div
              className={`max-w-3xl rounded-2xl p-4 text-xs font-sans leading-relaxed shadow-2xs ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-xs'
                  : 'bg-white text-text-primary border border-border-subtle rounded-tl-xs'
              }`}
            >
              {/* Text Answer */}
              <div className="whitespace-pre-wrap">{msg.text}</div>

              {/* Structured Table Render if available */}
              {msg.table && Array.isArray(msg.table) && msg.table.length > 0 && (
                <div className="mt-4 pt-3 border-t border-border-subtle overflow-x-auto">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
                      Structured Data ({msg.table.length} rows)
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        const csvContent = [
                          Object.keys(msg.table[0]).join(','),
                          ...msg.table.map(row => Object.values(row).map(v => `"${v}"`).join(','))
                        ].join('\n');
                        const blob = new Blob([csvContent], { type: 'text/csv' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `ledger_data_${Date.now()}.csv`;
                        a.click();
                      }}
                      className="text-[11px] text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-[14px]">download</span> Export CSV
                    </button>
                  </div>
                  <table className="w-full text-left border-collapse text-[11px]">
                    <thead>
                      <tr className="border-b border-border-subtle bg-surface-soft">
                        {Object.keys(msg.table[0]).map((col) => (
                          <th key={col} className="py-1.5 px-2.5 font-semibold text-text-secondary capitalize">
                            {col.replace(/_/g, ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle">
                      {msg.table.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-surface-soft/60 transition-colors">
                          {Object.keys(msg.table[0]).map((col) => (
                            <td key={col} className="py-1.5 px-2.5 text-text-primary whitespace-nowrap">
                              {String(row[col] ?? '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Matplotlib Graph Render if available */}
              {msg.graph && (
                <div className="mt-4 pt-3 border-t border-border-subtle">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px] text-blue-600">bar_chart</span>
                      Visual Chart
                    </span>
                    <a
                      href={`data:image/png;base64,${msg.graph}`}
                      download="invoice_analysis_chart.png"
                      className="text-[11px] text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-[14px]">download</span> Download Image
                    </a>
                  </div>
                  <div className="rounded-xl overflow-hidden border border-border-subtle bg-white p-2">
                    <img
                      src={`data:image/png;base64,${msg.graph}`}
                      alt="Generated financial chart"
                      className="w-full h-auto object-contain rounded-lg"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-2 mb-1 px-1">
              <span className="font-sans text-[11px] font-medium text-text-secondary">Ledger AI</span>
            </div>
            <div className="bg-white border border-border-subtle rounded-2xl rounded-tl-xs p-4 text-xs font-sans text-text-secondary flex items-center gap-3 shadow-2xs">
              <span className="material-symbols-outlined text-[20px] text-blue-600 animate-spin">
                progress_activity
              </span>
              <span>Reasoning over invoice vectors with Groq LangGraph...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Shelf */}
      <div className="px-6 py-2 bg-white/70 border-t border-border-subtle overflow-x-auto flex items-center gap-2 shrink-0">
        <span className="text-[11px] font-medium text-text-secondary shrink-0 flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px] text-blue-600">lightbulb</span> Prompts:
        </span>
        {SUGGESTED_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSendMessage(prompt)}
            disabled={isLoading}
            className="text-[11px] px-2.5 py-1 rounded-full bg-surface-soft hover:bg-blue-50 hover:text-blue-600 border border-border-subtle text-text-secondary whitespace-nowrap transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Bottom Message Input Form */}
      <div className="p-4 sm:p-6 bg-white border-t border-border-subtle shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-3"
        >
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={sessionId ? "Ask anything about your invoices (totals, vendors, dates, charts)..." : "Ask a question (session will auto-initialize with sample data)..."}
              disabled={isLoading}
              className="w-full pl-4 pr-10 py-3 rounded-xl border border-border-subtle bg-[#F9F9FB] text-text-primary text-xs focus:bg-white focus:outline-none focus:border-blue-500 transition-colors shadow-2xs"
            />
            {input && (
              <button
                type="button"
                onClick={() => setInput('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
              >
                <span className="material-symbols-outlined text-[16px]">cancel</span>
              </button>
            )}
          </div>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-xs font-semibold flex items-center gap-2 transition-all shadow-sm shrink-0"
          >
            <span>Send</span>
            <span className="material-symbols-outlined text-[16px]">send</span>
          </button>
        </form>
      </div>

    </div>
  );
}
