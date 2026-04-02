import React, { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import ErrorBoundary from '@/components/ErrorBoundary';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import Dashboard from '@/pages/Dashboard';
import QueryInterface from '@/pages/QueryInterface';
import SatelliteCatalog from '@/pages/SatelliteCatalog';
import Index from '@/pages/Index';
import NotFound from '@/pages/NotFound';
import { QueryTemplate } from '@/types/satellite';

const queryClient = new QueryClient();

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);

  const toggleSidebar = () => setSidebarOpen(prev => !prev);
  const toggleTheme = () => {
    setIsDarkMode(prev => !prev);
    document.documentElement.classList.toggle('light');
  };

  const handleTemplateSelect = useCallback((template: QueryTemplate) => {
    navigate('/query', { state: { initialQuery: template.query } });
    setSidebarOpen(false); // Close sidebar on mobile after selection
  }, [navigate]);

  const handleNewQuery = useCallback(() => {
    navigate('/query', { state: { clearChat: true } });
    setSidebarOpen(false);
  }, [navigate]);

  return (
    <div className={`min-h-screen bg-background ${isDarkMode ? 'dark' : 'light'}`}>
      <div className="flex flex-col h-screen">
        <Header
          onToggleSidebar={toggleSidebar}
          isDarkMode={isDarkMode}
          onToggleTheme={toggleTheme}
        />
        <div className="flex flex-1 overflow-hidden relative">
          {/* Desktop sidebar */}
          <div className="hidden lg:block">
            <Sidebar
              isOpen={true}
              onTemplateSelect={handleTemplateSelect}
              onNewQuery={handleNewQuery}
              savedQueries={[]}
            />
          </div>
          {/* Mobile sidebar overlay */}
          {sidebarOpen && (
            <>
              <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
              <div className="fixed left-0 top-16 bottom-0 z-50 lg:hidden">
                <Sidebar
                  isOpen={true}
                  onTemplateSelect={handleTemplateSelect}
                  onNewQuery={handleNewQuery}
                  savedQueries={[]}
                />
              </div>
            </>
          )}
          {children}
        </div>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/dashboard" element={
                <AppLayout><main className="flex-1 overflow-y-auto p-6"><Dashboard /></main></AppLayout>
              } />
              <Route path="/query" element={
                <AppLayout><main className="flex-1 overflow-hidden"><QueryInterface /></main></AppLayout>
              } />
              <Route path="/catalog" element={
                <AppLayout><main className="flex-1 overflow-y-auto p-6"><SatelliteCatalog /></main></AppLayout>
              } />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
          <Toaster />
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
