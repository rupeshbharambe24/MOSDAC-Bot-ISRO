
import React from 'react';
import StatsCards from '@/components/dashboard/StatsCards';
import SatelliteGlobe from '@/components/globe/SatelliteGlobe';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  Calendar, 
  Satellite,
  Database,
  ArrowRight,
  Clock
} from 'lucide-react';
import { DataStats } from '@/types/satellite';

const Dashboard: React.FC = () => {
  const stats: DataStats = {
    totalSatellites: 24,
    activeMissions: 18,
    dataPoints: '2.4M',
    coverage: '94.2%',
    lastUpdated: '2m ago'
  };

  const recentActivities = [
    {
      id: 1,
      title: 'OCEANSAT-3 Data Update',
      description: 'New sea surface temperature data available',
      time: '5 minutes ago',
      type: 'data'
    },
    {
      id: 2,
      title: 'Cyclone Alert Generated',
      description: 'Bay of Bengal weather pattern analysis',
      time: '1 hour ago',
      type: 'alert'
    },
    {
      id: 3,
      title: 'RESOURCESAT-2A Orbit Adjustment',
      description: 'Satellite repositioned for better coverage',
      time: '3 hours ago',
      type: 'mission'
    }
  ];

  const quickActions = [
    { title: 'SST Analysis', description: 'Monitor sea temperatures', icon: '🌊' },
    { title: 'Weather Tracking', description: 'Track cyclones and storms', icon: '🌪️' },
    { title: 'Land Monitoring', description: 'Observe land use changes', icon: '🛰️' },
    { title: 'Air Quality', description: 'Monitor atmospheric conditions', icon: '🌫️' }
  ];

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-lg bg-gradient-to-r from-primary via-primary to-secondary p-8 text-white">
        <div className="relative z-10">
          <h1 className="text-3xl font-bold mb-2">Welcome to ISRO SatQuery</h1>
          <p className="text-xl opacity-90 mb-6">
            Intelligent satellite data analysis and Earth observation insights
          </p>
          <div className="flex flex-wrap gap-4">
            <Button className="bg-white text-primary hover:bg-white/90">
              Start New Query
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button variant="outline" className="border-white text-white hover:bg-white/10">
              View Documentation
            </Button>
          </div>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl transform translate-x-32 -translate-y-32" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-secondary/20 rounded-full blur-2xl transform -translate-x-24 translate-y-24" />
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Globe Visualization */}
        <div className="lg:col-span-2">
          <SatelliteGlobe />
        </div>

        {/* Recent Activities */}
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
              <Button variant="ghost" className="w-full text-sm">
                View All Activities
              </Button>
            </CardContent>
          </Card>

          {/* Quick Actions */}
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

      {/* Mission Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Satellite className="h-5 w-5 text-primary" />
            Active Missions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-4 bg-accent/20 rounded-lg">
              <div>
                <h4 className="font-medium">OCEANSAT-3</h4>
                <p className="text-sm text-muted-foreground">Ocean Color Monitor</p>
              </div>
              <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                Active
              </Badge>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent/20 rounded-lg">
              <div>
                <h4 className="font-medium">RESOURCESAT-2A</h4>
                <p className="text-sm text-muted-foreground">Land Observation</p>
              </div>
              <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                Active
              </Badge>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent/20 rounded-lg">
              <div>
                <h4 className="font-medium">CARTOSAT-3</h4>
                <p className="text-sm text-muted-foreground">High Resolution Imaging</p>
              </div>
              <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                Maintenance
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
