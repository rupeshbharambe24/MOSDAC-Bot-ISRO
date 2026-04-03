import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ThumbsUp, ThumbsDown, MessageSquare, TrendingDown,
  RefreshCw, FlaskConical, CheckCircle2, XCircle, Clock,
  Play,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';

// ── Feedback types ────────────────────────────────────────────────────────
interface DayStats { date: string; up: number; down: number }
interface FeedbackEntry {
  timestamp: string; message_id: string;
  query: string; response: string; type: 'up' | 'down';
}
interface FeedbackData {
  total: number; up: number; down: number; up_pct: number; down_pct: number;
  daily: DayStats[];
  top_disliked: { query: string; count: number }[];
  recent: FeedbackEntry[];
}

// ── Eval types ────────────────────────────────────────────────────────────
interface EvalDetail {
  query: string; passed: boolean;
  error?: string;
  expected?: any; got?: any;
  found?: string[]; missing?: string[];
  response_preview?: string; response_length?: number;
}
interface EvalMetric {
  metric: string; score: number | null;
  passed: number; total: number;
  skipped?: boolean; details: EvalDetail[];
}
interface EvalData {
  available: boolean; message?: string;
  timestamp?: string; elapsed_seconds?: number;
  overall_score?: number | null; offline?: boolean;
  metrics?: EvalMetric[];
}

// ════════════════════════════════════════════════════════════════════════════
// FEEDBACK TAB
// ════════════════════════════════════════════════════════════════════════════
const FeedbackTab: React.FC = () => {
  const [data, setData] = useState<FeedbackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch('/api/admin/feedback');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const fmtDate = (iso: string) =>
    new Date(iso).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
  const fmtTime = (iso: string) =>
    new Date(iso).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });

  if (loading) return <Spinner label="Loading feedback…" />;
  if (error) return <ErrorPanel msg={error} onRetry={fetchData} />;
  if (!data) return null;

  const chartData = data.daily.map(d => ({
    name: fmtDate(d.date), Helpful: d.up, 'Not helpful': d.down,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">User feedback analytics</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="h-3.5 w-3.5 mr-1" />Refresh
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={<MessageSquare className="h-5 w-5 text-primary" />}
          iconBg="bg-primary/10" label="Total feedback" value={data.total} />
        <StatCard icon={<ThumbsUp className="h-5 w-5 text-green-500" />}
          iconBg="bg-green-500/10" label="Helpful" value={data.up}
          sub={`${data.up_pct}%`} subColor="text-green-500" />
        <StatCard icon={<ThumbsDown className="h-5 w-5 text-red-500" />}
          iconBg="bg-red-500/10" label="Not helpful" value={data.down}
          sub={`${data.down_pct}%`} subColor="text-red-500" />
        <StatCard icon={<TrendingDown className="h-5 w-5 text-orange-500" />}
          iconBg="bg-orange-500/10" label="Satisfaction"
          value={data.total ? `${data.up_pct}%` : '—'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Bar chart */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Feedback — last 7 days</CardTitle>
          </CardHeader>
          <CardContent>
            {data.total === 0
              ? <Empty msg="No feedback yet." />
              : <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={chartData} barSize={12} barGap={4}>
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Helpful" fill="#22c55e" radius={[3,3,0,0]} />
                    <Bar dataKey="Not helpful" fill="#ef4444" radius={[3,3,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
            }
          </CardContent>
        </Card>

        {/* Top disliked */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Most disliked queries</CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_disliked.length === 0
              ? <Empty msg="None yet." />
              : <div className="space-y-3">
                  {data.top_disliked.map((item, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs leading-snug line-clamp-2">{item.query}</p>
                        <Badge variant="destructive" className="shrink-0 text-xs">{item.count}</Badge>
                      </div>
                      {i < data.top_disliked.length - 1 && <div className="border-b" />}
                    </div>
                  ))}
                </div>
            }
          </CardContent>
        </Card>
      </div>

      {/* Recent log */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Recent feedback</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {data.recent.length === 0
            ? <Empty msg="No feedback recorded yet." className="py-8 px-4" />
            : <ScrollArea className="h-80">
                <div className="divide-y">
                  {data.recent.map((entry, i) => (
                    <div key={i} className="px-4 py-3 hover:bg-accent/30 transition-colors">
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 shrink-0 ${entry.type === 'up' ? 'text-green-500' : 'text-red-500'}`}>
                          {entry.type === 'up'
                            ? <ThumbsUp className="h-4 w-4" />
                            : <ThumbsDown className="h-4 w-4" />}
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
          }
        </CardContent>
      </Card>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════════════════
// EVAL TAB
// ════════════════════════════════════════════════════════════════════════════
const RADAR_COLORS: Record<string, string> = {
  'Entity Extraction': '#38bdf8',
  'Query Expansion':   '#a78bfa',
  'Retrieval Quality': '#34d399',
  'Response Quality':  '#fbbf24',
};

const EvalTab: React.FC = () => {
  const [data, setData] = useState<EvalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch('/api/admin/eval');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const runEval = async () => {
    setRunning(true);
    setError(null);
    const prev = data?.timestamp;
    const startedAt = Date.now();

    try {
      const triggerRes = await fetch('/api/admin/eval/run', { method: 'POST' });
      if (!triggerRes.ok) throw new Error(`Failed to start eval: HTTP ${triggerRes.status}`);

      const poll = setInterval(async () => {
        // Timeout after 3 minutes
        if (Date.now() - startedAt > 180_000) {
          clearInterval(poll);
          setRunning(false);
          setError('Evaluation timed out after 3 minutes. Check the server logs or run manually: python tests/eval_suite.py');
          return;
        }
        try {
          const res = await fetch('/api/admin/eval');
          if (!res.ok) return;
          const d: EvalData = await res.json();
          if (d.available && d.timestamp !== prev) {
            setData(d);
            setRunning(false);
            clearInterval(poll);
          }
        } catch { /* ignore transient fetch errors during polling */ }
      }, 4000);
    } catch (e) {
      setRunning(false);
      setError(e instanceof Error ? e.message : 'Failed to start evaluation');
    }
  };

  if (loading) return <Spinner label="Loading eval results…" />;
  if (error) return <ErrorPanel msg={error} onRetry={fetchData} />;

  const noResults = !data?.available;

  const radarData = data?.metrics
    ?.filter(m => m.score !== null && !m.skipped)
    .map(m => ({ metric: m.metric.replace(' ', '\n'), score: m.score })) ?? [];

  const fmtTs = (iso?: string) => iso
    ? new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
    : '—';

  return (
    <div className="space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            Pipeline quality metrics — entity extraction, retrieval, response quality
          </p>
          {data?.timestamp && (
            <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Last run: {fmtTs(data.timestamp)}
              {data.elapsed_seconds != null && ` · ${data.elapsed_seconds}s`}
              {data.offline && <Badge variant="secondary" className="text-xs ml-1">offline mode</Badge>}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={running}>
            <RefreshCw className="h-3.5 w-3.5 mr-1" />Refresh
          </Button>
          <Button size="sm" onClick={runEval} disabled={running}>
            {running
              ? <><RefreshCw className="h-3.5 w-3.5 mr-1 animate-spin" />Running…</>
              : <><Play className="h-3.5 w-3.5 mr-1" />Run Evaluation</>
            }
          </Button>
        </div>
      </div>

      {noResults ? (
        <Card>
          <CardContent className="py-16 text-center">
            <FlaskConical className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">{data?.message ?? 'No eval results yet.'}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Click <strong>Run Evaluation</strong> above, or run{' '}
              <code className="bg-muted px-1 rounded">python tests/eval_suite.py</code> manually.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Overall + radar */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6 flex flex-col items-center justify-center h-full gap-2">
                <p className="text-xs text-muted-foreground">Overall Score</p>
                <p className={`text-5xl font-bold ${
                  (data?.overall_score ?? 0) >= 80 ? 'text-green-500'
                  : (data?.overall_score ?? 0) >= 60 ? 'text-yellow-500'
                  : 'text-red-500'
                }`}>
                  {data?.overall_score ?? '—'}
                  {data?.overall_score != null ? '%' : ''}
                </p>
                <Badge variant={
                  (data?.overall_score ?? 0) >= 80 ? 'default'
                  : (data?.overall_score ?? 0) >= 60 ? 'secondary'
                  : 'destructive'
                }>
                  {(data?.overall_score ?? 0) >= 80 ? 'Good'
                   : (data?.overall_score ?? 0) >= 60 ? 'Fair'
                   : 'Needs work'}
                </Badge>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="pb-0">
                <CardTitle className="text-sm font-medium">Per-metric scores</CardTitle>
              </CardHeader>
              <CardContent>
                {radarData.length < 2
                  ? (
                    // Fallback bar chart when we don't have enough metrics for radar
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={data?.metrics?.filter(m => m.score !== null).map(m => ({
                        name: m.metric, score: m.score,
                      })) ?? []} barSize={32}>
                        <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(v: any) => `${v}%`} />
                        <Bar dataKey="score" fill="#38bdf8" radius={[4,4,0,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <ResponsiveContainer width="100%" height={200}>
                      <RadarChart data={radarData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
                        <Radar dataKey="score" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.25} />
                      </RadarChart>
                    </ResponsiveContainer>
                  )
                }
              </CardContent>
            </Card>
          </div>

          {/* Per-metric detail cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data?.metrics?.map(m => (
              <Card key={m.metric} className="overflow-hidden">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <span style={{ color: RADAR_COLORS[m.metric] ?? '#888' }}>●</span>
                      {m.metric}
                    </CardTitle>
                    {m.skipped
                      ? <Badge variant="secondary">skipped</Badge>
                      : <span className={`text-sm font-bold ${
                          (m.score ?? 0) >= 80 ? 'text-green-500'
                          : (m.score ?? 0) >= 60 ? 'text-yellow-500'
                          : 'text-red-500'
                        }`}>{m.score}%</span>
                    }
                  </div>
                  {!m.skipped && (
                    <p className="text-xs text-muted-foreground">{m.passed}/{m.total} passed</p>
                  )}
                </CardHeader>
                <CardContent className="pt-0">
                  {/* Progress bar */}
                  {!m.skipped && m.score !== null && (
                    <div className="w-full h-1.5 bg-muted rounded-full mb-3">
                      <div
                        className={`h-full rounded-full transition-all ${
                          m.score >= 80 ? 'bg-green-500'
                          : m.score >= 60 ? 'bg-yellow-500'
                          : 'bg-red-500'
                        }`}
                        style={{ width: `${m.score}%` }}
                      />
                    </div>
                  )}
                  {/* Test list — collapsed by default, expand on click */}
                  <button
                    className="text-xs text-muted-foreground hover:text-foreground w-full text-left"
                    onClick={() => setExpanded(expanded === m.metric ? null : m.metric)}
                  >
                    {expanded === m.metric ? '▲ Hide details' : '▼ Show test details'}
                  </button>
                  {expanded === m.metric && (
                    <div className="mt-2 space-y-1 max-h-52 overflow-y-auto pr-1">
                      {m.details.map((d, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs py-1 border-b last:border-0">
                          {d.passed
                            ? <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0 mt-0.5" />
                            : <XCircle     className="h-3.5 w-3.5 text-red-500   shrink-0 mt-0.5" />
                          }
                          <div className="flex-1 min-w-0">
                            <p className="truncate text-foreground">{d.query}</p>
                            {d.error && <p className="text-red-400">{d.error}</p>}
                            {d.missing && d.missing.length > 0 && (
                              <p className="text-muted-foreground">
                                Missing: {d.missing.join(', ')}
                              </p>
                            )}
                            {d.response_preview && !d.passed && (
                              <p className="text-muted-foreground line-clamp-2">{d.response_preview}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

// ════════════════════════════════════════════════════════════════════════════
// SHARED HELPERS
// ════════════════════════════════════════════════════════════════════════════
const Spinner: React.FC<{ label: string }> = ({ label }) => (
  <div className="flex items-center justify-center h-64 gap-2">
    <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
    <span className="text-sm text-muted-foreground">{label}</span>
  </div>
);

const ErrorPanel: React.FC<{ msg: string; onRetry: () => void }> = ({ msg, onRetry }) => (
  <div className="flex flex-col items-center justify-center h-64 gap-3">
    <p className="text-destructive text-sm">{msg}</p>
    <Button variant="outline" size="sm" onClick={onRetry}>Retry</Button>
  </div>
);

const Empty: React.FC<{ msg: string; className?: string }> = ({ msg, className = 'py-8 text-center' }) => (
  <p className={`text-sm text-muted-foreground ${className}`}>{msg}</p>
);

interface StatCardProps {
  icon: React.ReactNode; iconBg: string;
  label: string; value: React.ReactNode;
  sub?: string; subColor?: string;
}
const StatCard: React.FC<StatCardProps> = ({ icon, iconBg, label, value, sub, subColor }) => (
  <Card>
    <CardContent className="pt-5">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${iconBg}`}>{icon}</div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
          {sub && <p className={`text-xs ${subColor ?? ''}`}>{sub}</p>}
        </div>
      </div>
    </CardContent>
  </Card>
);

// ════════════════════════════════════════════════════════════════════════════
// ROOT COMPONENT
// ════════════════════════════════════════════════════════════════════════════
const AdminDashboard: React.FC = () => (
  <div className="space-y-4">
    <div>
      <h2 className="text-2xl font-bold">Admin Dashboard</h2>
      <p className="text-sm text-muted-foreground">Feedback analytics and pipeline evaluation</p>
    </div>

    <Tabs defaultValue="feedback">
      <TabsList>
        <TabsTrigger value="feedback" className="flex items-center gap-1.5">
          <ThumbsUp className="h-3.5 w-3.5" />Feedback
        </TabsTrigger>
        <TabsTrigger value="eval" className="flex items-center gap-1.5">
          <FlaskConical className="h-3.5 w-3.5" />Eval Metrics
        </TabsTrigger>
      </TabsList>

      <TabsContent value="feedback" className="mt-4">
        <FeedbackTab />
      </TabsContent>
      <TabsContent value="eval" className="mt-4">
        <EvalTab />
      </TabsContent>
    </Tabs>
  </div>
);

export default AdminDashboard;
