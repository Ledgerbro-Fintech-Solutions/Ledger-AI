import React, { useState } from 'react';
import Logo, { LogoIcon } from '../components/Logo';
import InvoicesTab from './dashboard/InvoicesTab';
import ExportsTab from './dashboard/ExportsTab';
import FoldersTab from './dashboard/FoldersTab';
import ReportsTab from './dashboard/ReportsTab';
import SettingsTab from './dashboard/SettingsTab';
import ChatbotTab from './dashboard/ChatbotTab';
import PhotoToCsvTab from './dashboard/PhotoToCsvTab';

const KPI_DATA = [
  {
    title: 'Invoices Processed',
    value: '2,481',
    change: '+18.4%',
    period: 'vs last month',
    icon: 'receipt_long',
    isPositive: true
  },
  {
    title: 'Processed Value',
    value: '$48.7M',
    period: 'August 2026',
    icon: 'payments'
  }
];

const RECENT_INVOICES = [
  {
    id: 'INV-2026-0842',
    vendor: 'Dell Technologies',
    date: 'Aug 14, 2026',
    amount: '$2,450.00',
    confidence: '91%',
    status: 'Needs Review',
    statusColor: 'amber'
  },
  {
    id: 'INV-2026-0841',
    vendor: 'ABC Technologies',
    date: 'Aug 14, 2026',
    amount: '$12,890.50',
    confidence: '99%',
    status: 'Completed',
    statusColor: 'emerald'
  },
  {
    id: 'XYZ-992-B',
    vendor: 'XYZ Manufacturing',
    date: 'Aug 13, 2026',
    amount: '$4,200.00',
    confidence: '98%',
    status: 'Completed',
    statusColor: 'emerald'
  },
  {
    id: 'PRM-00192',
    vendor: 'Prime Components',
    date: 'Aug 13, 2026',
    amount: '$850.25',
    confidence: '76%',
    status: 'Needs Review',
    statusColor: 'amber'
  }
];

const ACTIVITY_BARS = [
  { height: '40%', val: 120, label: 'Aug 1' },
  { height: '55%', val: 165, label: 'Aug 3' },
  { height: '30%', val: 90, label: 'Aug 5' },
  { height: '70%', val: 210, label: 'Aug 7' },
  { height: '45%', val: 135, label: 'Aug 9' },
  { height: '60%', val: 180, label: 'Aug 11' },
  { height: '85%', val: 284, label: 'Aug 14', active: true },
  { height: '50%', val: 150, label: 'Aug 16' },
  { height: '65%', val: 195, label: 'Aug 18' },
  { height: '40%', val: 120, label: 'Aug 20' },
  { height: '35%', val: 105, label: 'Aug 22' },
  { height: '75%', val: 225, label: 'Aug 24' },
  { height: '90%', val: 270, label: 'Aug 27' },
  { height: '55%', val: 165, label: 'Aug 29' },
  { height: '60%', val: 180, label: 'Aug 30' }
];

export default function DashboardPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [timeRange, setTimeRange] = useState('30D');
  const [selectedInvoices, setSelectedInvoices] = useState([]);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);

  const toggleSelectAll = () => {
    if (selectedInvoices.length === RECENT_INVOICES.length) {
      setSelectedInvoices([]);
    } else {
      setSelectedInvoices(RECENT_INVOICES.map((inv) => inv.id));
    }
  };

  const toggleSelectOne = (id) => {
    if (selectedInvoices.includes(id)) {
      setSelectedInvoices(selectedInvoices.filter((item) => item !== id));
    } else {
      setSelectedInvoices([...selectedInvoices, id]);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#F9F9FB] text-text-primary font-sans antialiased">
      
      {/* Mobile Sidebar Backdrop */}
      {isMobileSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/20 backdrop-blur-xs z-30 md:hidden"
          onClick={() => setIsMobileSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar (Supports Expanded & Minimized Modes) */}
      <aside className={`fixed md:static inset-y-0 left-0 z-40 bg-white md:bg-surface-soft border-r border-border-subtle flex flex-col py-6 transition-all duration-300 ease-in-out shrink-0 ${
        isSidebarCollapsed ? 'w-[72px] px-2.5' : 'w-[240px] px-4'
      } ${
        isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        
        {/* Header with Logo & Minimize Toggle */}
        <div className={`mb-6 flex items-center ${isSidebarCollapsed ? 'flex-col gap-3 justify-center' : 'justify-between px-2'}`}>
          {isSidebarCollapsed ? (
            <>
              <button 
                type="button"
                onClick={() => setIsSidebarCollapsed(false)}
                title="Expand sidebar"
                className="hover:opacity-80 transition-opacity focus:outline-none"
              >
                <LogoIcon className="w-8 h-8 rounded-lg shadow-sm" />
              </button>
              <button 
                type="button"
                onClick={() => setIsSidebarCollapsed(false)}
                className="p-1 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors"
                title="Expand sidebar"
              >
                <span className="material-symbols-outlined text-[18px]">dock_to_right</span>
              </button>
            </>
          ) : (
            <>
              <div className="flex items-center">
                <Logo />
              </div>
              
              <div className="flex items-center gap-1">
                <button 
                  type="button"
                  onClick={() => setIsSidebarCollapsed(true)}
                  className="hidden md:flex p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors"
                  title="Minimize sidebar"
                >
                  <span className="material-symbols-outlined text-[18px]">dock_to_left</span>
                </button>
                <button 
                  type="button"
                  onClick={() => setIsMobileSidebarOpen(false)}
                  className="md:hidden text-text-secondary hover:text-text-primary p-1 rounded-lg"
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              </div>
            </>
          )}
        </div>

        {/* Workspace Switcher */}
        <div 
          className={`mb-6 border border-border-subtle rounded-xl bg-white hover:border-border-strong transition-colors cursor-pointer group shadow-2xs ${
            isSidebarCollapsed ? 'p-2 flex justify-center' : 'mx-1 px-3 py-2 flex items-center justify-between'
          }`}
          title="Acme Manufacturing"
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-6 h-6 rounded-md bg-surface-muted border border-border-subtle flex items-center justify-center text-xs font-semibold text-text-primary shrink-0">
              AM
            </div>
            {!isSidebarCollapsed && (
              <span className="font-sans text-xs font-medium text-text-primary truncate">
                Acme Manufacturing
              </span>
            )}
          </div>
          {!isSidebarCollapsed && (
            <span className="material-symbols-outlined text-text-secondary text-[16px] group-hover:text-text-primary">
              unfold_more
            </span>
          )}
        </div>

        {/* Navigation Menu */}
        <div className="flex-1 overflow-y-auto pr-0.5 space-y-6">
          
          {/* Main Pages */}
          <ul className="space-y-1">
            {[
              { id: 'Dashboard', icon: 'dashboard' },
              { id: 'OCR to CSV', icon: 'table_view' },
              { id: 'AI Assistant', icon: 'smart_toy' },
              { id: 'Invoices', icon: 'receipt_long' },
              { id: 'Exports', icon: 'ios_share' }
            ].map((item) => {
              const isActive = activeTab === item.id;
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    title={isSidebarCollapsed ? item.id : undefined}
                    onClick={() => {
                      setActiveTab(item.id);
                      setIsMobileSidebarOpen(false);
                    }}
                    className={`w-full flex items-center rounded-lg font-sans text-xs font-medium transition-all ${
                      isSidebarCollapsed ? 'justify-center py-2.5 px-0' : 'gap-3 px-3 py-2'
                    } ${
                      isActive
                        ? 'bg-white text-text-primary font-semibold shadow-2xs border border-border-subtle'
                        : 'text-text-secondary hover:bg-surface-muted hover:text-text-primary'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                    {!isSidebarCollapsed && <span>{item.id}</span>}
                  </button>
                </li>
              );
            })}
          </ul>

          {/* Library Section */}
          <div>
            {!isSidebarCollapsed && (
              <div className="font-sans text-[11px] text-text-secondary uppercase tracking-wider px-3 mb-2 font-medium">
                Library
              </div>
            )}
            <ul className="space-y-1">
              {[
                { id: 'Folders', icon: 'folder' },
                { id: 'Reports', icon: 'bar_chart' },
                { id: 'Settings', icon: 'settings' }
              ].map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    title={isSidebarCollapsed ? item.id : undefined}
                    onClick={() => {
                      setActiveTab(item.id);
                      setIsMobileSidebarOpen(false);
                    }}
                    className={`w-full flex items-center rounded-lg font-sans text-xs font-medium transition-all ${
                      isSidebarCollapsed ? 'justify-center py-2.5 px-0' : 'gap-3 px-3 py-2'
                    } ${
                      activeTab === item.id
                        ? 'bg-white text-text-primary font-semibold shadow-2xs border border-border-subtle'
                        : 'text-text-secondary hover:bg-surface-muted hover:text-text-primary'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                    {!isSidebarCollapsed && <span>{item.id}</span>}
                  </button>
                </li>
              ))}
            </ul>
          </div>

        </div>

        {/* User Profile Footer with Popup Menu */}
        <div className="mt-auto pt-4 border-t border-border-subtle relative">
          {isProfileMenuOpen && (
            <div className={`absolute bottom-full mb-2 bg-white border border-border-subtle rounded-xl shadow-lg p-2 z-50 space-y-1 ${
              isSidebarCollapsed ? 'left-0 w-48' : 'left-0 right-0'
            }`}>
              <button 
                type="button"
                onClick={() => {
                  setActiveTab('Settings');
                  setIsProfileMenuOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-sans font-medium text-text-primary hover:bg-surface-soft rounded-lg text-left transition-colors"
              >
                <span className="material-symbols-outlined text-[16px] text-text-secondary">settings</span>
                <span>Settings</span>
              </button>
              <button 
                type="button"
                onClick={() => {
                  setIsProfileMenuOpen(false);
                  if (onNavigate) onNavigate('landing');
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-sans font-medium text-red-600 hover:bg-red-50 rounded-lg text-left transition-colors"
              >
                <span className="material-symbols-outlined text-[16px] text-red-600">logout</span>
                <span>Sign Out</span>
              </button>
            </div>
          )}

          <button 
            type="button"
            onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
            className={`w-full flex items-center rounded-xl hover:bg-white hover:shadow-2xs transition-all text-left group border border-transparent hover:border-border-subtle ${
              isSidebarCollapsed ? 'justify-center p-2' : 'gap-3 px-2 py-2'
            }`}
            title="Omkar Phadatare (Free Tier)"
          >
            <div className="w-8 h-8 rounded-full bg-surface-muted border border-border-subtle flex items-center justify-center text-text-secondary group-hover:text-text-primary shrink-0">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
            {!isSidebarCollapsed && (
              <>
                <div className="flex-1 overflow-hidden">
                  <p className="font-sans text-xs font-medium text-text-primary truncate">Omkar Phadatare</p>
                  <p className="font-sans text-[11px] text-text-secondary truncate">Free Tier Workspace</p>
                </div>
                <span className="material-symbols-outlined text-text-secondary text-[16px]">
                  {isProfileMenuOpen ? 'expand_less' : 'more_vert'}
                </span>
              </>
            )}
          </button>
        </div>

      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full bg-[#F9F9FB] relative overflow-hidden">
        
        {/* Top Header Bar */}
        <header className="h-16 flex items-center justify-between px-6 lg:px-10 border-b border-border-subtle bg-white sticky top-0 z-20 shrink-0">
          
          {/* Left: Mobile Navigation Toggle only */}
          <div className="flex items-center w-8 md:w-auto">
            <button
              type="button"
              onClick={() => setIsMobileSidebarOpen(true)}
              className="md:hidden p-1.5 rounded-lg text-text-secondary hover:bg-surface-soft hover:text-text-primary"
              title="Open menu"
            >
              <span className="material-symbols-outlined text-[20px]">menu</span>
            </button>
          </div>

          {/* Center: Search Bar */}
          <div className="flex-1 max-w-md lg:max-w-lg mx-4">
            <div className="relative w-full">
              <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-[16px] text-text-secondary">
                search
              </span>
              <input
                type="text"
                placeholder="Search invoices, vendors, files..."
                className="w-full h-9 pl-10 pr-12 bg-surface-soft border border-border-subtle rounded-xl text-xs font-sans text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:border-primary focus:bg-white focus:shadow-2xs transition-all"
              />
              <span className="absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 bg-white border border-border-subtle rounded text-[10px] font-mono text-text-secondary">
                ⌘K
              </span>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            <button type="button" className="w-8 h-8 rounded-lg hover:bg-surface-soft text-text-secondary hover:text-text-primary flex items-center justify-center transition-colors">
              <span className="material-symbols-outlined text-[18px]">help</span>
            </button>

            <button type="button" className="w-8 h-8 rounded-lg hover:bg-surface-soft text-text-secondary hover:text-text-primary flex items-center justify-center transition-colors relative">
              <span className="material-symbols-outlined text-[18px]">notifications</span>
              <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-red-500 rounded-full"></span>
            </button>
          </div>

        </header>

        {/* Scrollable Canvas */}
        <div className="flex-1 overflow-y-auto p-6 lg:p-10 pb-20">
          <div className="max-w-[1240px] mx-auto">
            
            {/* Conditional Tab Rendering */}
            {activeTab === 'OCR to CSV' ? (
              <PhotoToCsvTab onNavigateTab={setActiveTab} />
            ) : activeTab === 'AI Assistant' ? (
              <ChatbotTab onNavigateTab={setActiveTab} />
            ) : activeTab === 'Invoices' ? (
              <InvoicesTab onNavigateTab={setActiveTab} />
            ) : activeTab === 'Exports' ? (
              <ExportsTab />
            ) : activeTab === 'Folders' ? (
              <FoldersTab />
            ) : activeTab === 'Reports' ? (
              <ReportsTab onNavigateTab={setActiveTab} />
            ) : activeTab === 'Settings' ? (
              <SettingsTab />
            ) : (
              /* Dashboard Home View */
              <div className="space-y-8 animate-float-slow">
                
                {/* Page Greeting Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                  <div>
                    <h1 className="font-sans text-2xl lg:text-3xl font-semibold text-text-primary tracking-tight mb-1.5">
                      Good afternoon, Omkar
                    </h1>
                    <p className="font-sans text-sm text-text-secondary max-w-xl">
                      Monitor invoice processing, review exceptions, and manage your financial data from one unified workspace.
                    </p>
                  </div>

                  <div className="flex items-center gap-2.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => setActiveTab('AI Assistant')}
                      className="h-10 px-4 bg-white hover:bg-surface-soft border border-border-subtle text-text-primary rounded-lg font-sans font-medium text-xs flex items-center gap-2 transition-all shadow-2xs"
                    >
                      <span className="material-symbols-outlined text-[18px] text-blue-600">smart_toy</span>
                      <span>Ask AI Assistant</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveTab('Invoices')}
                      className="h-10 px-5 bg-text-primary hover:bg-black text-white rounded-lg font-sans font-medium text-xs flex items-center gap-2 transition-all shadow-sm active:scale-[0.99]"
                    >
                      <span className="material-symbols-outlined text-[18px]">add</span>
                      <span>Upload Invoices</span>
                    </button>
                  </div>
                </div>

                {/* KPI Cards (Row of 2 Clean Highlights) */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {KPI_DATA.map((kpi, idx) => (
                    <div 
                      key={idx} 
                      className="bg-white border border-border-subtle rounded-xl p-5 flex flex-col justify-between shadow-2xs relative overflow-hidden"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <span className="font-sans text-xs font-medium text-text-secondary">
                          {kpi.title}
                        </span>
                        <span className="material-symbols-outlined text-[18px] text-text-secondary">
                          {kpi.icon}
                        </span>
                      </div>

                      <div>
                        <div className="font-sans text-2xl font-semibold text-text-primary tracking-tight">
                          {kpi.value}
                        </div>
                        <div className="flex items-center gap-1.5 mt-1.5 text-xs">
                          {kpi.change && (
                            <span className="text-primary font-medium flex items-center gap-0.5">
                              <span className="material-symbols-outlined text-[14px]">trending_up</span>
                              {kpi.change}
                            </span>
                          )}
                          {kpi.period && (
                            <span className="text-text-secondary text-[11px]">{kpi.period}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Main Grid: Activity Chart & Processing Status Gauge */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  
                  {/* Analytics Activity Chart (2 cols) */}
                  <div className="lg:col-span-2 bg-white border border-border-subtle rounded-2xl p-6 flex flex-col justify-between shadow-2xs">
                    <div className="flex justify-between items-center mb-6">
                      <div>
                        <h3 className="font-sans font-semibold text-base text-text-primary">
                          Invoice Processing Activity
                        </h3>
                        <p className="font-sans text-xs text-text-secondary mt-0.5">
                          Daily processed invoice volume & trend
                        </p>
                      </div>

                      {/* Time Range Pills */}
                      <div className="flex gap-1 bg-surface-soft p-1 rounded-lg border border-border-subtle">
                        {['30D', '90D', 'YTD'].map((t) => (
                          <button
                            type="button"
                            key={t}
                            onClick={() => setTimeRange(t)}
                            className={`px-2.5 py-1 rounded-md font-sans text-xs font-medium transition-all ${
                              timeRange === t
                                ? 'bg-white text-text-primary shadow-2xs font-semibold'
                                : 'text-text-secondary hover:text-text-primary'
                            }`}
                          >
                            {t}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Minimalist Bar Chart Representation with Green Active Bar */}
                    <div className="flex-1 flex items-end justify-between gap-1 h-[210px] relative pt-6">
                      {/* Y-axis labels */}
                      <div className="absolute left-0 top-0 bottom-6 flex flex-col justify-between text-[10px] font-sans text-text-secondary/60 pointer-events-none">
                        <span>300</span>
                        <span>150</span>
                        <span>0</span>
                      </div>

                      {/* Horizontal grid lines */}
                      <div className="absolute left-7 right-0 top-2 h-px bg-border-subtle/60 pointer-events-none"></div>
                      <div className="absolute left-7 right-0 top-1/2 h-px bg-border-subtle/60 pointer-events-none"></div>
                      <div className="absolute left-7 right-0 bottom-6 h-px bg-border-subtle pointer-events-none"></div>

                      {/* Bars */}
                      <div className="flex flex-1 items-end gap-1.5 sm:gap-2.5 ml-8 pb-6 h-full z-10">
                        {ACTIVITY_BARS.map((bar, i) => (
                          <div
                            key={i}
                            className={`flex-1 rounded-t-sm transition-all duration-300 relative group cursor-pointer ${
                              bar.active 
                                ? 'bg-emerald-500 hover:bg-emerald-600' 
                                : 'bg-surface-container-high hover:bg-emerald-500/40'
                            }`}
                            style={{ height: bar.height }}
                          >
                            {/* Hover Tooltip */}
                            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-[10px] font-sans px-2 py-1 rounded shadow-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-20">
                              {bar.label}: {bar.val}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* X-axis labels */}
                      <div className="absolute left-8 right-0 bottom-0 flex justify-between text-[10px] font-sans text-text-secondary">
                        <span>Aug 1</span>
                        <span>Aug 15</span>
                        <span>Aug 30</span>
                      </div>
                    </div>
                  </div>

                  {/* Processing Status Donut (1 col) - Vibrant Green Progress Bar */}
                  <div className="bg-white border border-border-subtle rounded-2xl p-6 flex flex-col items-center justify-between shadow-2xs">
                    <div className="w-full text-left mb-4">
                      <h3 className="font-sans font-semibold text-base text-text-primary">
                        Processing Status
                      </h3>
                      <p className="font-sans text-xs text-text-secondary mt-0.5">
                        Real-time pipeline breakdown
                      </p>
                    </div>

                    {/* Donut Gauge in Green */}
                    <div className="relative my-4 flex items-center justify-center">
                      <div className="w-32 h-32 rounded-full border-8 border-surface-soft flex items-center justify-center relative shadow-inner">
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                          <path
                            className="text-surface-soft"
                            strokeWidth="3.8"
                            stroke="currentColor"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                          <path
                            className="text-emerald-500"
                            strokeDasharray="92, 100"
                            strokeWidth="3.8"
                            strokeLinecap="round"
                            stroke="currentColor"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                        </svg>

                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <span className="font-sans text-2xl font-bold text-text-primary leading-none">92%</span>
                          <span className="font-sans text-[10px] text-emerald-600 font-medium mt-1">Processed</span>
                        </div>
                      </div>
                    </div>

                    {/* Status Breakdown List */}
                    <div className="w-full space-y-2.5 font-sans text-xs pt-2">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                          <span className="text-text-primary">Completed</span>
                        </div>
                        <span className="font-semibold text-text-primary">2,283</span>
                      </div>

                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                          <span className="text-text-primary">Needs Review</span>
                        </div>
                        <span className="font-semibold text-text-primary">27</span>
                      </div>

                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-border-strong"></span>
                          <span className="text-text-primary">Processing</span>
                        </div>
                        <span className="font-semibold text-text-primary">164</span>
                      </div>

                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-red-500"></span>
                          <span className="text-text-primary">Failed</span>
                        </div>
                        <span className="font-semibold text-text-primary">7</span>
                      </div>
                    </div>
                  </div>

                </div>

                {/* Lower Region: Full Width Recent Invoices Data Table */}
                <div className="w-full bg-white border border-border-subtle rounded-2xl overflow-hidden flex flex-col shadow-2xs">
                  <div className="p-4 border-b border-border-subtle flex justify-between items-center bg-surface-soft">
                    <div className="flex items-center gap-3">
                      <h3 className="font-sans font-semibold text-sm text-text-primary">
                        Recent Invoices
                      </h3>
                      <span className="text-xs text-text-secondary">
                        Showing 4 of 2,481
                      </span>
                    </div>

                    <button type="button" className="px-3 py-1.5 bg-white border border-border-subtle rounded-lg text-xs font-sans text-text-secondary hover:text-text-primary font-medium flex items-center gap-1.5 shadow-2xs">
                      <span className="material-symbols-outlined text-[14px]">filter_list</span>
                      <span>Filter</span>
                    </button>
                  </div>

                  <div className="overflow-x-auto flex-1">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border-subtle bg-surface-soft/60 text-xs font-sans font-medium text-text-secondary">
                          <th className="py-3 px-4 w-10">
                            <input
                              type="checkbox"
                              checked={selectedInvoices.length === RECENT_INVOICES.length}
                              onChange={toggleSelectAll}
                              className="rounded border-border-strong text-text-primary focus:ring-0"
                            />
                          </th>
                          <th className="py-3 px-4">Invoice</th>
                          <th className="py-3 px-4">Vendor</th>
                          <th className="py-3 px-4">Date</th>
                          <th className="py-3 px-4 text-right">Amount</th>
                          <th className="py-3 px-4 text-center">AI Confidence</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 w-10"></th>
                        </tr>
                      </thead>
                      <tbody className="font-sans text-xs text-text-primary divide-y divide-border-subtle/60">
                        {RECENT_INVOICES.map((inv) => {
                          const isChecked = selectedInvoices.includes(inv.id);
                          return (
                            <tr key={inv.id} className="hover:bg-surface-soft/80 transition-colors group">
                              <td className="py-3 px-4">
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  onChange={() => toggleSelectOne(inv.id)}
                                  className="rounded border-border-strong text-text-primary focus:ring-0"
                                />
                              </td>
                              <td className="py-3 px-4 font-semibold text-text-primary">
                                {inv.id}
                              </td>
                              <td className="py-3 px-4">
                                {inv.vendor}
                              </td>
                              <td className="py-3 px-4 text-text-secondary">
                                {inv.date}
                              </td>
                              <td className="py-3 px-4 text-right font-semibold">
                                {inv.amount}
                              </td>
                              <td className="py-3 px-4 text-center">
                                <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-medium ${
                                  parseInt(inv.confidence) >= 95 
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                                  : parseInt(inv.confidence) >= 90
                                  ? 'bg-blue-50 text-blue-700 border border-blue-200/60'
                                  : 'bg-amber-50 text-amber-700 border border-amber-200/60'
                                }`}>
                                  {inv.confidence}
                                </span>
                              </td>
                              <td className="py-3 px-4">
                                <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium ${
                                  inv.statusColor === 'emerald'
                                    ? 'bg-emerald-50 text-emerald-700'
                                    : 'bg-amber-50 text-amber-800'
                                }`}>
                                  <span className={`w-1.5 h-1.5 rounded-full ${
                                    inv.statusColor === 'emerald' ? 'bg-emerald-500' : 'bg-amber-500'
                                  }`}></span>
                                  {inv.status}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button type="button" className="opacity-0 group-hover:opacity-100 text-text-secondary hover:text-text-primary p-1">
                                  <span className="material-symbols-outlined text-[16px]">more_vert</span>
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className="p-3 border-t border-border-subtle flex justify-center bg-surface-soft">
                    <button 
                      type="button" 
                      onClick={() => setActiveTab('Invoices')}
                      className="font-sans text-xs font-semibold text-text-primary hover:underline"
                    >
                      View All Invoices
                    </button>
                  </div>
                </div>

                {/* AI Insights & Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* AI Operational Insight */}
                  <div className="bg-[#1A1A1A] rounded-2xl p-6 text-white relative overflow-hidden flex flex-col justify-center min-h-[150px] shadow-sm">
                    <div className="absolute right-0 top-0 w-36 h-36 bg-emerald-500/20 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>
                    <div className="flex items-start gap-3.5 z-10">
                      <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-emerald-400 shrink-0">
                        <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
                      </div>
                      <div>
                        <h4 className="font-sans text-xs font-semibold uppercase tracking-wider text-emerald-300 mb-1">
                          Operational Insight
                        </h4>
                        <p className="font-sans text-xs text-white/90 leading-relaxed max-w-md font-normal">
                          <strong>92% automated throughput</strong> this week. Extraction models are performing with high precision across standard multi-page invoices.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Quick Actions Grid */}
                  <div className="bg-white border border-border-subtle rounded-2xl p-4 grid grid-cols-2 gap-3 shadow-2xs">
                    {[
                      { label: 'Upload Invoices', icon: 'upload_file' },
                      { label: 'Process Existing', icon: 'play_arrow' },
                      { label: 'Review Queue', icon: 'fact_check' },
                      { label: 'Create Export', icon: 'download' }
                    ].map((action, i) => (
                      <button 
                        key={i}
                        type="button"
                        onClick={() => setActiveTab('Invoices')}
                        className="flex flex-col items-start justify-center p-3.5 rounded-xl border border-border-subtle hover:border-border-strong hover:bg-surface-soft transition-all text-left group"
                      >
                        <span className="material-symbols-outlined mb-1.5 text-text-secondary group-hover:text-text-primary text-[20px]">
                          {action.icon}
                        </span>
                        <span className="font-sans font-semibold text-xs text-text-primary">
                          {action.label}
                        </span>
                      </button>
                    ))}
                  </div>

                </div>

              </div>
            )}

          </div>
        </div>

      </main>

    </div>
  );
}
