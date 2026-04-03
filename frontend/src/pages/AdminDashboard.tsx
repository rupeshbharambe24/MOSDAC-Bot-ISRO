import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ThumbsUp, ThumbsDown, MessageSquare, TrendingDown, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface DayStats {
  date: string;
  up: number;
  down: number;
}

interface FeedbackEntry {
  timestamp: string;
  message_id: string;
  query: string;
  response: string;
  type: 'up' | 'down';
}

interface FeedbackData {
  total: number;
  up: number;
  down: number;
  up_pct: number;
  down_pct: number;
  daily: DayStats[];
  top_disliked: { query: string; count: number }[];
  recent: FeedbackEntry[];
}

const AdminDashboard: React.FC = () => {
  const [data, setData] = useState<FeedbackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/admin/feedback');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load feedback data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const fmtDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
  };

  const fmtTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading feedback data…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <p className="text-destructive text-sm">{error}</p>
        <Button variant="outline" size="sm" onClick={fetchData}>Retry</Button>
      </div>
    );
  }

  if (!data) return null;

  const chartData = data.daily.map(d => ({
    name: fmtDate(d.date),
    Helpful: d.up,
    'Not helpful': d.down,
  }));

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Admin Dashboard</h2>
          <p className="text-sm text-muted-foreground">User feedback analytics</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="h-3.5 w-3.5 mr-1" />
          Refresh
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <MessageSquare className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total feedback</p>
                <p className="text-2xl font-bold">{data.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <ThumbsUp className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Helpful</p>
                <p className="text-2xl font-bold">{data.up}</p>
                <p className="text-xs text-green-500">{data.up_pct}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/10 rounded-lg">
                <ThumbsDown className="h-5 w-5 text-red-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Not helpful</p>
                <p className="text-2xl font-bold">{data.down}</p>
                <p className="text-xs text-red-500">{data.down_pct}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500/10 rounded-lg">
                <TrendingDown className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Satisfaction</p>
                <p className="text-2xl font-bold">
                  {data.total ? data.up_pct : '—'}
                  {data.total ? '%' : ''}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trend chart + top disliked side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Feedback — last 7 days</CardTitle>
          </CardHeader>
          <CardContent>
            {data.total === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">No feedback yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} barSize={12} barGap={4}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="Helpful" fill="#22c55e" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="Not helpful" fill="#ef4444" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Most disliked queries</CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_disliked.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">None yet.</p>
            ) : (
              <div className="space-y-3">
                {data.top_disliked.map((item, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs leading-snug text-foreground line-clamp-2">{item.query}</p>
                      <Badge variant="destructive" className="shrink-0 text-xs">{item.count}</Badge>
                    </div>
                    {i < data.top_disliked.length - 1 && <div className="border-b" />}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent feedback log */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Recent feedback</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {data.recent.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center px-4">No feedback recorded yet.</p>
          ) : (
            <ScrollArea className="h-80">
              <div className="divide-y">
                {data.recent.map((entry, i) => (
                  <div key={i} className="px-4 py-3 hover:bg-accent/30 transition-colors">
                    <div className="flex items-start gap-3">
                      <div className={`mt-0.5 shrink-0 ${entry.type === 'up' ? 'text-green-500' : 'text-red-500'}`}>
                        {entry.type === 'up'
                          ? <ThumbsUp className="h-4 w-4" />
                          : <ThumbsDown className="h-4 w-4" />
                        }
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{entry.query || '(no query)'}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{entry.response}</p>
                      </div>
                      <span className="text-xs text-muted-foreground shrink-0">{fmtTime(entry.timestamp)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;
