
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Satellite, 
  Database, 
  Globe, 
  Clock,
  TrendingUp,
  Activity
} from 'lucide-react';
import { DataStats } from '@/types/satellite';

interface StatsCardsProps {
  stats: DataStats;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats }) => {
  const statItems = [
    {
      title: 'Active Satellites',
      value: stats.totalSatellites.toString(),
      subtitle: `${stats.activeMissions} missions`,
      icon: Satellite,
      trend: '+2 this month',
      color: 'text-primary'
    },
    {
      title: 'Data Points',
      value: stats.dataPoints,
      subtitle: 'Processed today',
      icon: Database,
      trend: '+15% from yesterday',
      color: 'text-green-500'
    },
    {
      title: 'Global Coverage',
      value: stats.coverage,
      subtitle: 'Earth surface',
      icon: Globe,
      trend: 'Complete coverage',
      color: 'text-blue-500'
    },
    {
      title: 'Last Updated',
      value: stats.lastUpdated,
      subtitle: 'Real-time sync',
      icon: Clock,
      trend: 'Live monitoring',
      color: 'text-secondary'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statItems.map((item, index) => (
        <Card key={index} className="relative overflow-hidden group hover:shadow-lg transition-all duration-300">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {item.title}
            </CardTitle>
            <div className={`p-2 rounded-lg bg-background/50 ${item.color}`}>
              <item.icon className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col space-y-2">
              <div className="text-2xl font-bold">{item.value}</div>
              <p className="text-xs text-muted-foreground">{item.subtitle}</p>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-3 w-3 text-green-500" />
                <Badge variant="secondary" className="text-xs">
                  {item.trend}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default StatsCards;
