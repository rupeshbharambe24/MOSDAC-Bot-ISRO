
import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import Dashboard from '@/pages/Dashboard';
import QueryInterface from '@/pages/QueryInterface';
import SatelliteCatalog from '@/pages/SatelliteCatalog';
import Index from '@/pages/Index';
import { QueryTemplate } from '@/types/satellite';

const queryClient = new QueryClient();

const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [savedQueries] = useState<QueryTemplate[]>([]);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('light');
  };

  const handleTemplateSelect = (template: QueryTemplate) => {
    console.log('Selected template:', template);
    // This will be handled by the chat interface directly
  };

  const handleNewQuery = () => {
    // Clear chat state - this will be handled by the QueryInterface component
    console.log('New query initiated');
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <div className={`min-h-screen bg-background ${isDarkMode ? 'dark' : 'light'}`}>
          <BrowserRouter>
            <Routes>
              {/* Landing page route */}
              <Route path="/" element={<Index />} />
              
              {/* App routes with sidebar */}
              <Route path="/*" element={
                <div className="flex flex-col h-screen">
                  <Header 
                    onToggleSidebar={toggleSidebar}
                    isDarkMode={isDarkMode}
                    onToggleTheme={toggleTheme}
                  />
                  
                  <div className="flex flex-1 overflow-hidden">
                    <Routes>
                      <Route path="/dashboard" element={
                        <>
                          <Sidebar 
                            isOpen={sidebarOpen}
                            onTemplateSelect={handleTemplateSelect}
                            onNewQuery={handleNewQuery}
                            savedQueries={savedQueries}
                          />
                          <main className="flex-1 overflow-y-auto p-6">
                            <Dashboard />
                          </main>
                        </>
                      } />
                      <Route path="/query" element={
                        <>
                          <Sidebar 
                            isOpen={sidebarOpen}
                            onTemplateSelect={handleTemplateSelect}
                            onNewQuery={handleNewQuery}
                            savedQueries={savedQueries}
                          />
                          <main className="flex-1 overflow-hidden">
                            <QueryInterface />
                          </main>
                        </>
                      } />
                      <Route path="/catalog" element={
                        <>
                          <Sidebar 
                            isOpen={sidebarOpen}
                            onTemplateSelect={handleTemplateSelect}
                            onNewQuery={handleNewQuery}
                            savedQueries={savedQueries}
                          />
                          <main className="flex-1 overflow-y-auto p-6">
                            <SatelliteCatalog />
                          </main>
                        </>
                      } />
                    </Routes>
                  </div>
                </div>
              } />
            </Routes>
          </BrowserRouter>
        </div>
        <Toaster />
        <Sonner />
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
