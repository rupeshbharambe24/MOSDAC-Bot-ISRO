
import React, { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Satellite, Globe, Activity } from 'lucide-react';

const SatelliteGlobe: React.FC = () => {
  const globeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Simulate satellite positions animation
    const satellites = globeRef.current?.querySelectorAll('.satellite-dot');
    if (satellites) {
      satellites.forEach((sat, index) => {
        const element = sat as HTMLElement;
        element.style.animationDelay = `${index * 2}s`;
      });
    }
  }, []);

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-primary" />
          Global Coverage Map
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative w-full h-80 bg-gradient-to-b from-blue-950 via-blue-900 to-blue-800 rounded-lg overflow-hidden">
          {/* Earth representation */}
          <div 
            ref={globeRef}
            className="absolute inset-4 bg-gradient-to-br from-green-800 via-green-600 to-blue-500 rounded-full relative overflow-hidden"
            style={{
              backgroundImage: `
                radial-gradient(circle at 30% 20%, rgba(34, 197, 94, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 70% 40%, rgba(59, 130, 246, 0.4) 0%, transparent 50%),
                radial-gradient(circle at 20% 80%, rgba(34, 197, 94, 0.2) 0%, transparent 50%)
              `
            }}
          >
            {/* Satellite orbital paths */}
            <div className="absolute inset-0">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="absolute inset-0 border border-white/20 rounded-full animate-pulse"
                  style={{
                    transform: `scale(${1 + i * 0.2}) rotate(${i * 30}deg)`,
                    animationDelay: `${i * 0.5}s`
                  }}
                />
              ))}
            </div>

            {/* Satellite dots */}
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="satellite-dot absolute w-2 h-2 bg-secondary rounded-full pulse-glow"
                style={{
                  top: `${20 + Math.random() * 60}%`,
                  left: `${20 + Math.random() * 60}%`,
                  animationDuration: `${2 + Math.random() * 2}s`
                }}
              />
            ))}

            {/* Data coverage overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/10 to-transparent animate-pulse" />
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-secondary rounded-full" />
              <span className="text-xs text-white">Active Satellites</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-primary rounded-full" />
              <span className="text-xs text-white">Data Coverage</span>
            </div>
          </div>

          {/* Stats overlay */}
          <div className="absolute top-4 right-4 space-y-2">
            <Badge className="bg-black/50 text-white">
              <Activity className="h-3 w-3 mr-1" />
              Live
            </Badge>
            <Badge className="bg-black/50 text-white">
              <Satellite className="h-3 w-3 mr-1" />
              24 Active
            </Badge>
          </div>
        </div>

        {/* Quick stats below globe */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="text-center">
            <div className="text-lg font-bold text-primary">85%</div>
            <div className="text-xs text-muted-foreground">Ocean Coverage</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-green-500">92%</div>
            <div className="text-xs text-muted-foreground">Land Coverage</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-secondary">24/7</div>
            <div className="text-xs text-muted-foreground">Monitoring</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SatelliteGlobe;
