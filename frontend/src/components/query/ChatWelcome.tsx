
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Satellite } from 'lucide-react';

interface ChatWelcomeProps {
  onTemplateSelect: (template: string) => void;
}

const sampleQueries = [
  "Show SST data for Arabian Sea",
  "Track cyclone patterns in Bay of Bengal", 
  "Land use changes in Western Ghats",
  "Air quality monitoring for Delhi NCR",
  "Monsoon rainfall analysis for Kerala",
  "Coastal erosion tracking using satellite imagery"
];

const ChatWelcome: React.FC<ChatWelcomeProps> = ({ onTemplateSelect }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center space-y-6 p-8">
      <div className="relative">
        <div className="w-20 h-20 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
          <Satellite className="h-10 w-10 text-white" />
        </div>
        <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
      </div>
      
      <div className="space-y-3">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          Welcome to ISRO SatQuery
        </h2>
        <p className="text-muted-foreground max-w-md">
          Ask me anything about satellite data, Earth observations, or space missions. 
          I can help you analyze oceanographic data, track weather patterns, and explore our planet from space.
        </p>
      </div>
      
      <div className="space-y-3">
        <p className="text-sm font-medium text-muted-foreground">Try these sample queries:</p>
        <div className="flex flex-wrap gap-2 max-w-2xl justify-center">
          {sampleQueries.map((query, index) => (
            <Badge
              key={index}
              variant="outline"
              className="cursor-pointer hover:bg-primary hover:text-white transition-colors px-3 py-1"
              onClick={() => onTemplateSelect(query)}
            >
              {query}
            </Badge>
          ))}
        </div>
      </div>
      
      <div className="text-xs text-muted-foreground mt-8 space-y-1">
        <p>🛰️ Covers 12 ISRO satellites — INSAT-3D, SCATSAT-1, Oceansat, Megha-Tropiques and more</p>
        <p>🗺️ Responses auto-detect regions and show an interactive coverage map</p>
        <p>💬 Multi-turn conversation — ask follow-up questions in context</p>
      </div>
    </div>
  );
};

export default ChatWelcome;
