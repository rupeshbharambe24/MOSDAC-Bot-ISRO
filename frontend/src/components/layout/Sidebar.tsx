
import React, { useState } from 'react';
import {
  MessageSquare,
  Database,
  BookmarkPlus,
  Satellite,
  Map,
  BarChart3,
  FileText,
  Cloud,
  Waves,
  Eye,
  History,
  Star,
  ChevronDown,
  ChevronRight,
  RotateCcw,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { QueryTemplate } from '@/types/satellite';
import { useNavigate } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onTemplateSelect: (template: QueryTemplate) => void;
  onNewQuery: () => void;
  savedQueries: QueryTemplate[];
}

const queryTemplates: QueryTemplate[] = [
  {
    id: '1',
    title: 'SST Analysis',
    description: 'Sea Surface Temperature trends',
    query: 'Show me sea surface temperature data for the Arabian Sea in the last 30 days',
    category: 'oceanography',
    icon: 'Waves'
  },
  {
    id: '2',
    title: 'Cyclone Tracking',
    description: 'Tropical cyclone monitoring',
    query: 'Track cyclone formation in the Bay of Bengal this monsoon season',
    category: 'meteorology',
    icon: 'Cloud'
  },
  {
    id: '3',
    title: 'Land Use Change',
    description: 'LULC analysis',
    query: 'Analyze land use changes in the Western Ghats over the past 5 years',
    category: 'land',
    icon: 'Map'
  },
  {
    id: '4',
    title: 'Air Quality Index',
    description: 'Atmospheric pollution',
    query: 'Monitor air quality index for major Indian cities this week',
    category: 'atmosphere',
    icon: 'Eye'
  }
];

const satelliteIcons = [
  { name: 'INSAT-3D', status: 'active', type: 'weather' },
  { name: 'SCATSAT-1', status: 'active', type: 'ocean' },
  { name: 'OCEANSAT-3', status: 'active', type: 'ocean' },
  { name: 'RESOURCESAT-2A', status: 'active', type: 'land' }
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onTemplateSelect, onNewQuery, savedQueries }) => {
  const navigate = useNavigate();
  const [expandedSections, setExpandedSections] = useState({
    templates: true,
    satellites: false,
    saved: true
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const iconMap = {
    Waves,
    Cloud,
    Map,
    Eye
  };

  const handleNewQuery = () => {
    onNewQuery();
    // Add animation class temporarily
    const button = document.querySelector('#new-query-btn');
    if (button) {
      button.classList.add('scale-95');
      setTimeout(() => button.classList.remove('scale-95'), 150);
    }
  };

  if (!isOpen) return null;

  return (
    <aside className="w-80 h-[calc(100vh-4rem)] bg-card border-r flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
            <Satellite className="h-4 w-4 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-sm">MOSDAC</h2>
            <p className="text-xs text-muted-foreground">ISRO Data Portal</p>
          </div>
        </div>
        
        <Button 
          id="new-query-btn"
          onClick={handleNewQuery}
          className="w-full gradient-primary text-white hover:opacity-90 transition-all duration-200"
          style={{ backgroundColor: '#FF9933' }}
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          New Query
        </Button>
      </div>

      <ScrollArea className="flex-1 custom-scrollbar">
        <div className="p-4 space-y-6">
          {/* Quick Templates */}
          <div>
            <button
              onClick={() => toggleSection('templates')}
              className="flex items-center justify-between w-full text-sm font-medium mb-3 hover:text-primary transition-colors"
              aria-label="Toggle quick templates"
            >
              <span>Quick Templates</span>
              {expandedSections.templates ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
            
            {expandedSections.templates && (
              <div className="space-y-2">
                {queryTemplates.map((template) => {
                  const IconComponent = iconMap[template.icon as keyof typeof iconMap];
                  return (
                    <Card
                      key={template.id}
                      className="p-3 cursor-pointer hover:bg-accent/50 transition-colors group"
                      onClick={() => onTemplateSelect(template)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                          <IconComponent className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium truncate">{template.title}</h4>
                          <p className="text-xs text-muted-foreground mt-1">{template.description}</p>
                          <Badge variant="secondary" className="mt-2 text-xs">
                            {template.category}
                          </Badge>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>

          {/* Satellite Quick Access */}
          <div>
            <button
              onClick={() => toggleSection('satellites')}
              className="flex items-center justify-between w-full text-sm font-medium mb-3 hover:text-primary transition-colors"
              aria-label="Toggle satellite database"
            >
              <span>Satellite Quick Access</span>
              {expandedSections.satellites ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
            
            {expandedSections.satellites && (
              <div className="space-y-2">
                {satelliteIcons.map((satellite, index) => (
                  <Card key={index} className="p-3 cursor-pointer hover:bg-accent/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <Satellite className={`h-4 w-4 ${
                        satellite.type === 'weather' ? 'text-blue-500' :
                        satellite.type === 'ocean' ? 'text-cyan-500' :
                        'text-green-500'
                      }`} />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{satellite.name}</p>
                        <p className="text-xs text-muted-foreground capitalize">{satellite.type} monitoring</p>
                      </div>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${satellite.status === 'active' ? 'text-green-600 border-green-600' : ''}`}
                      >
                        {satellite.status}
                      </Badge>
                    </div>
                  </Card>
                ))}
                
                <Button variant="ghost" className="w-full text-xs" size="sm">
                  <Database className="h-3 w-3 mr-2" />
                  View All Satellites
                </Button>
              </div>
            )}
          </div>

          {/* Saved Queries */}
          <div>
            <button
              onClick={() => toggleSection('saved')}
              className="flex items-center justify-between w-full text-sm font-medium mb-3 hover:text-primary transition-colors"
              aria-label="Toggle saved queries"
            >
              <span>Recent Queries</span>
              {expandedSections.saved ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
            
            {expandedSections.saved && (
              <div className="space-y-2">
                <Card className="p-3 cursor-pointer hover:bg-accent/50 transition-colors">
                  <div className="flex items-start gap-3">
                    <History className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">Monsoon rainfall patterns</p>
                      <p className="text-xs text-muted-foreground">2 hours ago</p>
                    </div>
                    <Star className="h-3 w-3 text-yellow-500" />
                  </div>
                </Card>
                
                <Card className="p-3 cursor-pointer hover:bg-accent/50 transition-colors">
                  <div className="flex items-start gap-3">
                    <History className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">Arctic ice coverage trends</p>
                      <p className="text-xs text-muted-foreground">1 day ago</p>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </div>
      </ScrollArea>

      {/* Admin link */}
      <div className="p-3 border-t">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-xs text-muted-foreground hover:text-foreground"
          onClick={() => navigate('/admin')}
        >
          <ShieldCheck className="h-3.5 w-3.5 mr-2" />
          Admin Dashboard
        </Button>
      </div>
    </aside>
  );
};

export default Sidebar;
