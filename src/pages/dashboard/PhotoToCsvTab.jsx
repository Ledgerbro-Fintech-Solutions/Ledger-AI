import React, { useState, useRef } from 'react';

export default function PhotoToCsvTab({ onNavigateTab }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeView, setActiveView] = useState('table'); // 'table' | 'csv'
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setError(null);
    setResult(null);

    if (selectedFile.type.startsWith('image/')) {
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const loadSampleAwsInvoice = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      const resp = await fetch('/sample-aws-invoice.png');
      const blob = await resp.blob();
      const sampleFile = new File([blob], 'aws_invoice_sample.png', { type: 'image/png' });
      setFile(sampleFile);
      setPreviewUrl('/sample-aws-invoice.png');
      await processFile(sampleFile);
    } catch (err) {
      setError(`Failed to load sample: ${err.message}`);
      setIsProcessing(false);
    }
  };

  const processFile = async (fileToUpload) => {
    const targetFile = fileToUpload || file;
    if (!targetFile) return;

    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', targetFile);

    try {
      const response = await fetch('/api/ocr/photo-to-csv', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.error || 'Failed to extract tabular data from photo');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownloadCsv = () => {
    if (!result?.csv_data) return;
    const blob = new Blob([result.csv_data], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const safeBase = (result.filename || 'extracted_invoice').replace(/\.[^/.]+$/, '');
    link.href = url;
    link.setAttribute('download', `${safeBase}_tabular.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleCopyCsv = () => {
    if (!result?.csv_data) return;
    navigator.clipboard.writeText(result.csv_data);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="space-y-6 animate-float-slow pb-16">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="font-sans text-2xl lg:text-3xl font-semibold text-text-primary tracking-tight mb-1.5 flex items-center gap-2.5">
            <span>OCR Photo to Tabular CSV</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              Groq Vision AI
            </span>
          </h1>
          <p className="font-sans text-sm text-text-secondary max-w-2xl">
            Upload any invoice photo, receipt, or scanned document. The AI extracts line-item tables, dates, and amounts, converting them into structured CSV data.
          </p>
        </div>

        <button
          type="button"
          onClick={loadSampleAwsInvoice}
          disabled={isProcessing}
          className="h-9 px-3.5 bg-surface-soft hover:bg-surface-muted text-text-primary border border-border-subtle rounded-lg font-sans text-xs font-medium flex items-center gap-2 transition-all shadow-2xs shrink-0 disabled:opacity-50"
        >
          <span className="material-symbols-outlined text-[16px] text-amber-600">receipt</span>
          <span>Load & Test Sample AWS Invoice</span>
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-[18px] text-red-500">error</span>
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-800">
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      )}

      {/* Main 2-Column Responsive Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: File Dropzone & Image Preview */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white border border-border-subtle rounded-2xl p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-sans text-xs font-semibold text-text-primary uppercase tracking-wider">
                Upload Photo / Scan
              </span>
              {file && (
                <span className="font-sans text-[11px] text-text-secondary truncate max-w-[160px]">
                  {file.name}
                </span>
              )}
            </div>

            {/* Dropzone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                previewUrl ? 'border-blue-400 bg-blue-50/20' : 'border-border-subtle hover:border-blue-500 bg-[#F9F9FB]'
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={(e) => handleFileChange(e.target.files?.[0])}
                accept=".png,.jpg,.jpeg,.webp,.pdf"
                className="hidden"
              />

              {previewUrl ? (
                <div className="space-y-3">
                  <div className="max-h-64 overflow-hidden rounded-lg border border-border-subtle shadow-xs bg-white flex items-center justify-center">
                    <img
                      src={previewUrl}
                      alt="Uploaded invoice preview"
                      className="max-h-64 object-contain w-full"
                    />
                  </div>
                  <p className="text-[11px] text-text-secondary">
                    Click or drag another image to replace
                  </p>
                </div>
              ) : (
                <div className="py-6 space-y-2">
                  <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                    <span className="material-symbols-outlined text-[24px]">add_photo_alternate</span>
                  </div>
                  <p className="font-sans text-xs font-medium text-text-primary">
                    Drop invoice photo here, or <span className="text-blue-600 underline">browse</span>
                  </p>
                  <p className="font-sans text-[11px] text-text-tertiary">
                    Supports PNG, JPG, JPEG, WebP, and PDF (up to 50MB)
                  </p>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                onClick={() => processFile()}
                disabled={!file || isProcessing}
                className="flex-1 h-10 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl font-sans text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-sm"
              >
                {isProcessing ? (
                  <>
                    <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                    <span>Extracting Tables...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">table_chart</span>
                    <span>Extract Tabular Data</span>
                  </>
                )}
              </button>

              {file && (
                <button
                  type="button"
                  onClick={() => {
                    setFile(null);
                    setPreviewUrl(null);
                    setResult(null);
                  }}
                  className="h-10 px-3 bg-surface-soft hover:bg-surface-muted text-text-secondary hover:text-text-primary rounded-xl text-xs transition-colors"
                  title="Clear image"
                >
                  <span className="material-symbols-outlined text-[18px]">delete</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Extracted Tabular Output & Export Actions */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <div className="bg-white border border-border-subtle rounded-2xl p-5 shadow-2xs space-y-5">
              
              {/* Header Bar with Export Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border-subtle">
                <div>
                  <h2 className="font-sans text-sm font-semibold text-text-primary flex items-center gap-2">
                    <span>Extracted Tabular Output</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {result.row_count} rows detected
                    </span>
                  </h2>
                  <p className="font-sans text-[11px] text-text-secondary">
                    {result.filename} • Ready for export
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <div className="border border-border-subtle rounded-lg p-0.5 flex bg-surface-soft text-[11px]">
                    <button
                      type="button"
                      onClick={() => setActiveView('table')}
                      className={`px-2.5 py-1 rounded-md transition-colors ${
                        activeView === 'table' ? 'bg-white text-text-primary font-semibold shadow-2xs' : 'text-text-secondary'
                      }`}
                    >
                      Table
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveView('csv')}
                      className={`px-2.5 py-1 rounded-md transition-colors ${
                        activeView === 'csv' ? 'bg-white text-text-primary font-semibold shadow-2xs' : 'text-text-secondary'
                      }`}
                    >
                      Raw CSV
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={handleCopyCsv}
                    className="h-8 px-2.5 bg-surface-soft hover:bg-surface-muted text-text-primary rounded-lg font-sans text-xs flex items-center gap-1.5 border border-border-subtle transition-colors shadow-2xs"
                    title="Copy CSV to clipboard"
                  >
                    <span className="material-symbols-outlined text-[14px]">
                      {copied ? 'check' : 'content_copy'}
                    </span>
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleDownloadCsv}
                    className="h-8 px-3 bg-text-primary hover:bg-black text-white rounded-lg font-sans text-xs font-medium flex items-center gap-1.5 transition-all shadow-xs"
                    title="Download extracted CSV file"
                  >
                    <span className="material-symbols-outlined text-[14px]">download</span>
                    <span>Download CSV</span>
                  </button>
                </div>
              </div>

              {/* Invoice Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-sans text-xs">
                <div className="p-3 rounded-xl bg-surface-soft border border-border-subtle">
                  <span className="text-[10px] text-text-secondary block mb-0.5">Vendor / Provider</span>
                  <span className="font-semibold text-text-primary truncate block" title={result.invoice_details?.vendor_name}>
                    {result.invoice_details?.vendor_name || 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-surface-soft border border-border-subtle">
                  <span className="text-[10px] text-text-secondary block mb-0.5">Invoice #</span>
                  <span className="font-semibold text-text-primary truncate block">
                    {result.invoice_details?.invoice_number || 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-surface-soft border border-border-subtle">
                  <span className="text-[10px] text-text-secondary block mb-0.5">Invoice Date</span>
                  <span className="font-semibold text-text-primary truncate block">
                    {result.invoice_details?.invoice_date || 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-200">
                  <span className="text-[10px] text-emerald-700 block mb-0.5">Total Amount</span>
                  <span className="font-bold text-emerald-800 text-sm truncate block">
                    {result.currency || '$'}{Number(result.total_amount ?? 0).toFixed(2)}
                  </span>
                </div>
              </div>

              {/* View 1: Interactive Table */}
              {activeView === 'table' ? (
                <div className="border border-border-subtle rounded-xl overflow-hidden shadow-2xs">
                  <div className="max-h-96 overflow-y-auto overflow-x-auto">
                    <table className="w-full text-left font-sans text-[11px] border-collapse">
                      <thead className="bg-surface-soft sticky top-0 border-b border-border-subtle text-text-secondary font-semibold">
                        <tr>
                          {result.columns.map((col) => (
                            <th key={col} className="p-2.5 whitespace-nowrap">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle">
                        {result.rows.map((row, idx) => (
                          <tr key={idx} className="hover:bg-surface-soft/60 transition-colors">
                            {result.columns.map((col) => (
                              <td key={col} className="p-2.5 text-text-primary whitespace-nowrap">
                                {String(row[col] ?? '')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                /* View 2: Raw CSV Code Block */
                <div className="border border-border-subtle rounded-xl overflow-hidden bg-slate-900 text-slate-100 font-mono text-[11px] p-3 max-h-96 overflow-auto">
                  <pre className="whitespace-pre">{result.csv_data}</pre>
                </div>
              )}

              {/* Footer Assistance Bridge */}
              <div className="pt-2 flex items-center justify-between text-xs text-text-secondary">
                <span>Want to ask questions or plot graphs with this data?</span>
                <button
                  type="button"
                  onClick={() => onNavigateTab && onNavigateTab('AI Assistant')}
                  className="inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-700 font-medium text-xs"
                >
                  <span>Open in AI Assistant</span>
                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </button>
              </div>

            </div>
          ) : (
            /* Placeholder state before upload */
            <div className="bg-white border border-border-subtle rounded-2xl p-12 text-center shadow-2xs flex flex-col items-center justify-center min-h-[380px] space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-surface-soft border border-border-subtle text-text-secondary flex items-center justify-center">
                <span className="material-symbols-outlined text-[28px] text-blue-600">table_rows</span>
              </div>
              <h3 className="font-sans text-base font-semibold text-text-primary">
                No Photo Processed Yet
              </h3>
              <p className="font-sans text-xs text-text-secondary max-w-sm">
                Select an invoice photo on the left or click "Load & Test Sample AWS Invoice" above to extract tables and generate your CSV immediately.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
