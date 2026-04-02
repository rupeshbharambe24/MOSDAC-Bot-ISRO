import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StatsCards from '@/components/dashboard/StatsCards';
import SatelliteGlobe from '@/components/globe/SatelliteGlobe';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Satellite,
  Database,
  ArrowRight,
  Clock,
  Loader2,
} from 'lucide-react';
import { DataStats } from '@/types/satellite';

const DEFAULT_STATS: DataStats = {
  totalSatellites: 24,
  activeMissions: 18,
  dataPoints: '2.4M',
  coverage: '94.2%',
  lastUpdated: 'offline',
};

interface ApiSatellite {
  name: string;
  source?: string;
  instruments: string[];
  products: string[];
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DataStats>(DEFAULT_STATS);
  const [satellites, setSatellites] = useState<ApiSatellite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [statsRes, satsRes] = await Promise.allSettled([
          fetch('/api/stats'),
          fetch('/api/satellites'),
        ]);

        if (statsRes.status === 'fulfilled' && statsRes.value.ok) {
          const data = await statsRes.value.json();
          const s = data.stats;
          setStats({
            totalSatellites: s.satellite_count || 0,
            activeMissions: s.instrument_count || 0,
            dataPoints: String(s.data_product_count || 0),
            coverage: `${s.region_count || 0} regions`,
            lastUpdated: 'live',
          });
        }

        if (satsRes.status === 'fulfilled' && satsRes.value.ok) {
          const data = await satsRes.value.json();
          setSatellites(data.satellites || []);
        }
      } catch {
        // Keep defaults
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const recentActivities = [
    { id: 1, title: 'OCEANSAT-3 Data Update', description: 'New sea surface temperature data available', time: '5 minutes ago', type: 'data' },
    { id: 2, title: 'Cyclone Alert Generated', description: 'Bay of Bengal weather pattern analysis', time: '1 hour ago', type: 'alert' },
    { id: 3, title: 'RESOURCESAT-2A Orbit Adjustment', description: 'Satellite repositioned for better coverage', time: '3 hours ago', type: 'mission' },
  ];

  const quickActions = [
    { title: 'SST Analysis', description: 'Monitor sea temperatures', icon: '\u{1F30A}', query: 'Show me sea surface temperature data for the Arabian Sea' },
    { title: 'Weather Tracking', description: 'Track cyclones and storms', icon: '\u{1F32A}\uFE0F', query: 'Track cyclone formation in the Bay of Bengal' },
    { title: 'Land Monitoring', description: 'Observe land use changes', icon: '\u{1F6F0}\uFE0F', query: 'Analyze land use changes in the Western Ghats' },
    { title: 'Air Quality', description: 'Monitor atmospheric conditions', icon: '\u{1F32B}\uFE0F', query: 'Monitor air quality index for major Indian cities' },
  ];

  const displaySatellites = satellites.length > 0
    ? satellites.slice(0, 3).map(s => ({ name: s.name, mission: s.instruments[0] || 'Satellite', status: 'active' as const }))
    : [
        { name: 'OCEANSAT-3', mission: 'Ocean Color Monitor', status: 'active' as const },
        { name: 'RESOURCESAT-2A', mission: 'Land Observation', status: 'active' as const },
        { name: 'CARTOSAT-3', mission: 'High Resolution Imaging', status: 'maintenance' as const },
      ];

  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-lg bg-gradient-to-r from-primary via-primary to-secondary p-8 text-white">
        <div className="relative z-10">
          <h1 className="text-3xl font-bold mb-2">Welcome to ISRO SatQuery</h1>
          <p className="text-xl opacity-90 mb-6">
            Intelligent satellite data analysis and Earth observation insights
          </p>
          <div className="flex flex-wrap gap-4">
            <Button className="bg-white text-primary hover:bg-white/90" onClick={() => navigate('/query')}>
              Start New Query
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button variant="outline" className="border-white text-white hover:bg-white/10" onClick={() => window.open('https://www.mosdac.gov.in', '_blank')}>
              View Documentation
            </Button>
          </div>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl transform translate-x-32 -translate-y-32" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-secondary/20 rounded-full blur-2xl transform -translate-x-24 translate-y-24" />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-8 rounded-lg" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-3 w-20 mb-2" />
                <Skeleton className="h-5 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <StatsCards stats={stats} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SatelliteGlobe />
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-primary" />
                Recent Activities
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentActivities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent/50 transition-colors">
                  <div className={`w-2 h-2 rounded-full mt-2 ${
                    activity.type === 'data' ? 'bg-blue-500' :
                    activity.type === 'alert' ? 'bg-red-500' : 'bg-green-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate">{activity.title}</h4>
                    <p className="text-xs text-muted-foreground mt-1">{activity.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-primary" />
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  className="w-full justify-start h-auto p-3 hover:bg-accent/50"
                  onClick={() => navigate('/query', { state: { initialQuery: action.query } })}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{action.icon}</span>
                    <div className="text-left">
                      <div className="text-sm font-medium">{action.title}</div>
                      <div className="text-xs text-muted-foreground">{action.description}</div>
                    </div>
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Satellite className="h-5 w-5 text-primary" />
            Active Missions
            {satellites.length > 0 && (
              <Badge variant="secondary" className="ml-2 text-xs">Live from Knowledge Graph</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {displaySatellites.map((sat, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 bg-accent/20 rounded-lg cursor-pointer hover:bg-accent/30 transition-colors"
                onClick={() => navigate('/query', { state: { initialQuery: `Tell me about ${sat.name}` } })}
              >
                <div>
                  <h4 className="font-medium">{sat.name}</h4>
                  <p className="text-sm text-muted-foreground">{sat.mission}</p>
                </div>
                <Badge className={
                  sat.status === 'active'
                    ? 'bg-green-500/10 text-green-500 border-green-500/20'
                    : 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
                }>
                  {sat.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
