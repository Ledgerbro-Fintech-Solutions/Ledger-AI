import React, { useState, useRef } from 'react';

const SUMMARY_METRICS = [
  {
    title: 'Total Invoices',
    value: '2,481',
    period: 'All workspaces'
  },
  {
    title: 'Updated This Month',
    value: '42',
    period: 'August 2026'
  },
  {
    title: 'Verified & Ready',
    value: '18',
    statusDot: 'bg-emerald-500'
  },
  {
    title: 'Pending Review',
    value: '7',
    statusDot: 'bg-amber-500'
  }
];

const INVOICE_BATCHES = [
  {
    id: 1,
    name: 'August 2026 Raw Extract',
    source: 'August 2026 / 243 invoices',
    rows: '1,284',
    status: 'Ready',
    statusColor: 'emerald',
    tags: ['#August', '#Verified'],
    created: 'Aug 28, 2026',
    columns: '14',
    lastExport: '2 hours ago',
    items: [
      { id: 'INV-842', vendor: 'Acme Corp', amount: '$4,200.00' },
      { id: 'INV-843', vendor: 'TechFlow', amount: '$1,150.50' },
      { id: 'INV-844', vendor: 'Staples', amount: '$84.99' },
      { id: 'INV-845', vendor: 'AWS Cloud', amount: '$8,490.20' }
    ]
  },
  {
    id: 2,
    name: 'Q3 Vendor Discrepancies',
    source: 'Multiple Folders / 84 invoices',
    rows: '412',
    status: 'Draft',
    statusColor: 'amber',
    tags: ['#Q3', '#Finance'],
    created: 'Aug 26, 2026',
    columns: '12',
    lastExport: 'Yesterday',
    items: [
      { id: 'INV-790', vendor: 'Dell Tech', amount: '$2,450.00' },
      { id: 'INV-791', vendor: 'Prime Logistics', amount: '$920.00' },
      { id: 'INV-792', vendor: 'Global Office', amount: '$310.40' }
    ]
  },
  {
    id: 3,
    name: 'Annual Tax Export 2025',
    source: '2025 Archive / 1,420 invoices',
    rows: '8,402',
    status: 'Ready',
    statusColor: 'emerald',
    tags: ['#Tax2025', '#Archived'],
    created: 'Aug 15, 2026',
    columns: '16',
    lastExport: '3 days ago',
    items: [
      { id: 'INV-2025-01', vendor: 'Enterprise Corp', amount: '$14,250.00' },
      { id: 'INV-2025-02', vendor: 'Alpha Hosting', amount: '$3,800.00' },
      { id: 'INV-2025-03', vendor: 'Stripe Payments', amount: '$740.00' }
    ]
  },
  {
    id: 4,
    name: 'Hardware & Infrastructure Q2',
    source: 'Server Cluster / 56 invoices',
    rows: '920',
    status: 'Ready',
    statusColor: 'emerald',
    tags: ['#Infra', '#Q2'],
    created: 'Aug 10, 2026',
    columns: '10',
    lastExport: '1 week ago',
    items: [
      { id: 'INV-601', vendor: 'Supermicro Server', amount: '$18,900.00' },
      { id: 'INV-602', vendor: 'Cisco Routing', amount: '$4,120.00' }
    ]
  }
];

export default function InvoicesTab({ onNavigateTab }) {
  const [batches, setBatches] = useState(INVOICE_BATCHES);
  const [selectedBatchId, setSelectedBatchId] = useState(1);
  const [isPreviewOpen, setIsPreviewOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCheckboxes, setSelectedCheckboxes] = useState([1]);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'grid'
  const [isProcessing, setIsProcessing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const fileInputRef = useRef(null);

  const triggerToast = (msg, actionText = null, onAction = null) => {
    setToastMessage({ text: msg, actionText, onAction });
    setTimeout(() => {
      setToastMessage(null);
    }, 5500);
  };

  const selectedBatch = batches.find((b) => b.id === selectedBatchId) || batches[0] || INVOICE_BATCHES[0];

  const filteredBatches = batches.filter((b) =>
    b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    b.source.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleSelectAll = () => {
    if (selectedCheckboxes.length === batches.length) {
      setSelectedCheckboxes([]);
    } else {
      setSelectedCheckboxes(batches.map((b) => b.id));
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    triggerToast(`Extracting structured data from ${files.length} invoice(s) using Groq Vision LLM...`);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const resp = await fetch('/extract-ocr-data', {
        method: 'POST',
        body: formData
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || err.error || 'Failed to extract invoice');
      }

      const resData = await resp.json();
      const extractedItems = [];
      let totalRows = 0;

      resData.data.forEach((doc) => {
        const vendor = doc.invoice_details?.vendor_name || 'Extracted Vendor';
        const invNum = doc.invoice_details?.invoice_number || 'INV-EXT';
        if (doc.line_items && doc.line_items.length > 0) {
          doc.line_items.forEach((item, idx) => {
            extractedItems.push({
              id: `${invNum}-${idx + 1}`,
              vendor: vendor,
              amount: `$${(item.total_price || 0).toFixed(2)}`
            });
            totalRows++;
          });
        } else {
          extractedItems.push({
            id: invNum,
            vendor: vendor,
            amount: `$${(doc.invoice_details?.total_amount || 0).toFixed(2)}`
          });
          totalRows++;
        }
      });

      const newBatch = {
        id: Date.now(),
        name: `Extracted Batch (${files[0].name})`,
        source: `Direct Upload / ${files.length} document(s)`,
        rows: totalRows.toString(),
        status: 'Ready',
        statusColor: 'emerald',
        tags: ['#AI_Extracted', '#GroqVision'],
        created: 'Just now',
        columns: '12',
        lastExport: 'Never',
        items: extractedItems,
        rawOcrData: resData
      };

      setBatches((prev) => [newBatch, ...prev]);
      setSelectedBatchId(newBatch.id);
      setSelectedCheckboxes([newBatch.id]);
      setIsPreviewOpen(true);
      triggerToast(
        `Extracted ${totalRows} line items successfully!`,
        'Ask AI Assistant',
        () => onNavigateTab && onNavigateTab('AI Assistant')
      );
    } catch (err) {
      triggerToast(`Upload error: ${err.message}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const toggleCheckbox = (id, e) => {
    e.stopPropagation();
    if (selectedCheckboxes.includes(id)) {
      setSelectedCheckboxes(selectedCheckboxes.filter((item) => item !== id));
    } else {
      setSelectedCheckboxes([...selectedCheckboxes, id]);
    }
  };

  const handleProcessSelected = () => {
    if (selectedCheckboxes.length === 0) return;
    setIsProcessing(true);
    triggerToast(`Combining and grouping ${selectedCheckboxes.length} document batches...`);

    setTimeout(() => {
      setIsProcessing(false);
      triggerToast(
        `Successfully combined into unified master report & folder!`,
        'View in Reports',
        () => onNavigateTab && onNavigateTab('Reports')
      );
    }, 1200);
  };

  return (
    <div className="space-y-8 animate-float-slow">
      
      {/* Action Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-text-primary text-white font-sans text-xs font-medium px-4 py-3 rounded-xl shadow-xl flex items-center gap-3 animate-fade-in border border-white/10">
          <span className="material-symbols-outlined text-emerald-400 text-[18px]">
            {isProcessing ? 'sync' : 'check_circle'}
          </span>
          <span>{toastMessage.text}</span>
          {toastMessage.actionText && toastMessage.onAction && (
            <button
              type="button"
              onClick={toastMessage.onAction}
              className="ml-2 px-2.5 py-1 bg-white text-text-primary rounded-md font-semibold hover:bg-surface-soft transition-colors"
            >
              {toastMessage.actionText}
            </button>
          )}
        </div>
      )}

      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="font-sans text-2xl lg:text-3xl font-semibold text-text-primary tracking-tight mb-1.5">
            Invoices & Data Library
          </h1>
          <p className="font-sans text-sm text-text-secondary max-w-xl">
            Upload invoices, select documents, and process combinations into unified folder reports.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.png,.jpg,.jpeg,.webp"
            multiple
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="h-10 px-5 bg-text-primary hover:bg-black text-white rounded-lg font-sans font-medium text-xs flex items-center gap-2 transition-all shadow-sm active:scale-[0.99] disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[18px]">
              {isUploading ? 'sync' : 'add'}
            </span>
            <span>{isUploading ? 'Processing with AI...' : 'Upload Invoices'}</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards (Row of 4) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {SUMMARY_METRICS.map((metric, idx) => (
          <div
            key={idx}
            className="bg-white border border-border-subtle rounded-xl p-5 shadow-2xs flex flex-col justify-between"
          >
            <div className="flex justify-between items-start mb-2">
              <span className="font-sans text-xs font-medium text-text-secondary">
                {metric.title}
              </span>
              {metric.statusDot && (
                <span className={`w-2 h-2 rounded-full ${metric.statusDot}`}></span>
              )}
            </div>

            <div>
              <div className="font-sans text-2xl font-semibold text-text-primary tracking-tight">
                {metric.value}
              </div>
              {metric.period && (
                <p className="font-sans text-[11px] text-text-secondary mt-1">
                  {metric.period}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Main Master-Detail Workspace: Table + Interactive Preview Drawer */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        
        {/* Table / Grid Container */}
        <div className="flex-1 w-full bg-white border border-border-subtle rounded-2xl overflow-hidden shadow-2xs flex flex-col min-h-[500px]">
          
          {/* Controls Toolbar with Process Button */}
          <div className="p-4 border-b border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface-soft">
            
            {/* Search Box */}
            <div className="relative flex-1 max-w-sm">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-[16px]">
                search
              </span>
              <input
                type="text"
                placeholder="Search sheets, vendors, invoices..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-9 pl-9 pr-3 bg-white border border-border-subtle rounded-lg text-xs font-sans text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:border-primary transition-all"
              />
            </div>

            {/* Action Buttons & View Mode Controls */}
            <div className="flex items-center gap-2.5">
              
              {/* Process Selected Button */}
              {selectedCheckboxes.length > 0 && (
                <button
                  type="button"
                  onClick={handleProcessSelected}
                  disabled={isProcessing}
                  className="h-8.5 px-3.5 bg-text-primary hover:bg-black text-white rounded-lg font-sans font-semibold text-xs flex items-center gap-1.5 transition-all shadow-xs active:scale-[0.98]"
                >
                  <span className="material-symbols-outlined text-[16px]">
                    {isProcessing ? 'sync' : 'auto_fix_high'}
                  </span>
                  <span>{isProcessing ? 'Combining...' : `Process Selected (${selectedCheckboxes.length})`}</span>
                </button>
              )}

              {/* View Mode Toggle */}
              <div className="flex border border-border-subtle rounded-lg overflow-hidden bg-white shadow-2xs">
                <button
                  type="button"
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 transition-colors ${
                    viewMode === 'list' ? 'bg-surface-soft text-text-primary font-bold' : 'text-text-secondary hover:text-text-primary'
                  }`}
                  title="List View"
                >
                  <span className="material-symbols-outlined text-[16px]">list</span>
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('grid')}
                  className={`p-1.5 transition-colors ${
                    viewMode === 'grid' ? 'bg-surface-soft text-text-primary font-bold' : 'text-text-secondary hover:text-text-primary'
                  }`}
                  title="Grid View"
                >
                  <span className="material-symbols-outlined text-[16px]">grid_view</span>
                </button>
              </div>
            </div>

          </div>

          {/* List View Table */}
          {viewMode === 'list' ? (
            <div className="overflow-x-auto flex-1">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border-subtle bg-surface-soft/60 text-xs font-sans font-medium text-text-secondary">
                    <th className="py-3 px-4 w-10">
                      <input
                        type="checkbox"
                        checked={selectedCheckboxes.length === INVOICE_BATCHES.length}
                        onChange={toggleSelectAll}
                        className="rounded border-border-strong text-text-primary focus:ring-0"
                      />
                    </th>
                    <th className="py-3 px-4">Document / Batch Name</th>
                    <th className="py-3 px-4">Source</th>
                    <th className="py-3 px-4 text-right">Rows</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 w-10"></th>
                  </tr>
                </thead>
                <tbody className="font-sans text-xs text-text-primary divide-y divide-border-subtle/60">
                  {filteredBatches.map((batch) => {
                    const isSelected = selectedBatchId === batch.id;
                    const isChecked = selectedCheckboxes.includes(batch.id);

                    return (
                      <tr
                        key={batch.id}
                        onClick={() => {
                          setSelectedBatchId(batch.id);
                          setIsPreviewOpen(true);
                        }}
                        className={`cursor-pointer transition-colors group ${
                          isSelected ? 'bg-surface-soft font-medium' : 'hover:bg-surface-soft/60'
                        }`}
                      >
                        <td className="py-3.5 px-4" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={(e) => toggleCheckbox(batch.id, e)}
                            className="rounded border-border-strong text-text-primary focus:ring-0"
                          />
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px] text-text-secondary">
                              description
                            </span>
                            <span className="font-semibold text-text-primary">
                              {batch.name}
                            </span>
                          </div>
                          <div className="flex gap-1 mt-1">
                            {batch.tags.map((tag, tIdx) => (
                              <span
                                key={tIdx}
                                className="px-1.5 py-0.2 bg-white text-text-secondary rounded text-[10px] border border-border-subtle font-sans"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </td>

                        <td className="py-3.5 px-4 text-text-secondary">
                          {batch.source}
                        </td>

                        <td className="py-3.5 px-4 text-right font-medium text-text-primary">
                          {batch.rows}
                        </td>

                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium ${
                              batch.statusColor === 'emerald'
                                ? 'bg-emerald-50 text-emerald-700'
                                : 'bg-amber-50 text-amber-800'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                batch.statusColor === 'emerald' ? 'bg-emerald-500' : 'bg-amber-500'
                              }`}
                            ></span>
                            {batch.status}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            className="opacity-0 group-hover:opacity-100 text-text-secondary hover:text-text-primary p-1"
                          >
                            <span className="material-symbols-outlined text-[16px]">more_vert</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            /* Grid View */
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
              {filteredBatches.map((batch) => {
                const isSelected = selectedBatchId === batch.id;
                return (
                  <div
                    key={batch.id}
                    onClick={() => {
                      setSelectedBatchId(batch.id);
                      setIsPreviewOpen(true);
                    }}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-text-primary bg-white shadow-xs'
                        : 'border-border-subtle bg-surface-soft hover:border-border-strong hover:bg-white'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-sans font-semibold text-xs text-text-primary">
                        {batch.name}
                      </span>
                      <span
                        className={`w-2 h-2 rounded-full ${
                          batch.statusColor === 'emerald' ? 'bg-emerald-500' : 'bg-amber-500'
                        }`}
                      ></span>
                    </div>
                    <p className="font-sans text-xs text-text-secondary mb-3">{batch.source}</p>
                    <div className="flex justify-between items-center text-xs text-text-secondary">
                      <span>{batch.rows} Line Items</span>
                      <span>{batch.created}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

        </div>

        {/* Live Preview Drawer (Right Panel) */}
        {isPreviewOpen && selectedBatch && (
          <div className="w-full lg:w-80 bg-white border border-border-subtle rounded-2xl overflow-hidden shadow-2xs flex flex-col shrink-0">
            
            {/* Drawer Header */}
            <div className="p-5 border-b border-border-subtle">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-sans font-semibold text-sm text-text-primary">
                    {selectedBatch.name}
                  </h3>
                  <span className="font-sans text-[11px] text-text-secondary">
                    Batch Metadata
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsPreviewOpen(false)}
                  className="text-text-secondary hover:text-text-primary p-1 rounded-lg hover:bg-surface-soft"
                  title="Close preview"
                >
                  <span className="material-symbols-outlined text-[16px]">close</span>
                </button>
              </div>

              {/* Metadata Details */}
              <div className="space-y-2 mb-5 font-sans text-xs">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Created</span>
                  <span className="text-text-primary font-medium">{selectedBatch.created}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Rows</span>
                  <span className="text-text-primary font-semibold">{selectedBatch.rows}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Columns</span>
                  <span className="text-text-primary font-medium">{selectedBatch.columns} cols</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Last Export</span>
                  <span className="text-text-primary font-medium">{selectedBatch.lastExport}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => onNavigateTab && onNavigateTab('AI Assistant')}
                  className="w-full h-9 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg font-sans font-medium text-xs flex items-center justify-center gap-1.5 transition-all shadow-2xs"
                >
                  <span className="material-symbols-outlined text-[16px]">smart_toy</span>
                  <span>Ask AI About This Batch</span>
                </button>
                <button
                  type="button"
                  onClick={() => onNavigateTab && onNavigateTab('Reports')}
                  className="w-full h-9 bg-text-primary hover:bg-black text-white rounded-lg font-sans font-medium text-xs transition-all shadow-xs active:scale-[0.99]"
                >
                  Open in Reports
                </button>
                <button
                  type="button"
                  onClick={() => onNavigateTab && onNavigateTab('Exports')}
                  className="w-full h-9 bg-white border border-border-subtle hover:border-border-strong text-text-primary rounded-lg font-sans font-medium text-xs flex items-center justify-center gap-1.5 transition-all shadow-2xs"
                >
                  <span className="material-symbols-outlined text-[16px]">download</span>
                  <span>Export</span>
                </button>
              </div>
            </div>

            {/* Embedded Live Data Preview Table */}
            <div className="p-4 bg-surface-soft flex-1">
              <div className="font-sans text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2.5">
                Data Preview
              </div>

              <div className="bg-white border border-border-subtle rounded-xl overflow-hidden shadow-2xs">
                <table className="w-full text-left font-sans text-[11px]">
                  <thead className="bg-surface-soft border-b border-border-subtle text-text-secondary font-medium">
                    <tr>
                      <th className="p-2">ID</th>
                      <th className="p-2">Vendor</th>
                      <th className="p-2 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle/60 text-text-primary">
                    {selectedBatch.items.map((item, iIdx) => (
                      <tr key={iIdx} className="hover:bg-surface-soft/60">
                        <td className="p-2 font-medium">{item.id}</td>
                        <td className="p-2 truncate max-w-[100px]">{item.vendor}</td>
                        <td className="p-2 text-right font-semibold">{item.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

      </div>

    </div>
  );
}
