import React, { useState, useEffect, useRef } from 'react';
import { Satellite, Moon, Sun, Menu, Search, Bell, ThumbsUp, ThumbsDown, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useNavigate } from 'react-router-dom';

interface FeedbackEntry {
  timestamp: string;
  query: string;
  type: 'up' | 'down';
}

interface HeaderProps {
  onToggleSidebar: () => void;
  isDarkMode: boolean;
  onToggleTheme: () => void;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar, isDarkMode, onToggleTheme }) => {
  const navigate = useNavigate();
  const [notifOpen, setNotifOpen] = useState(false);
  const [recent, setRecent] = useState<FeedbackEntry[]>([]);
  const [unread, setUnread] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch recent feedback for notification panel
  useEffect(() => {
    fetch('/api/admin/feedback')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        setRecent((data.recent ?? []).slice(0, 5));
        setUnread(data.down ?? 0); // show count of negative feedback as "needs attention"
      })
      .catch(() => {});
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    };
    if (notifOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [notifOpen]);

  const fmtTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' });
    } catch { return iso; }
  };

  return (
    <header className="h-16 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60 sticky top-0 z-50">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Satellite className="h-10 w-10 text-primary" />
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                SatSage
              </h1>
              <p className="text-xs text-muted-foreground">Satellite Data Intelligence</p>
            </div>
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search satellites, data, missions..."
              className="pl-10 bg-muted/50"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          {/* Notification bell */}
          <div className="relative" ref={dropdownRef}>
            <Button
              variant="ghost"
              size="icon"
              className="relative"
              onClick={() => setNotifOpen(o => !o)}
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
              {unread > 0 && (
                <span className="absolute -top-1 -right-1 h-4 w-4 bg-destructive rounded-full text-[10px] flex items-center justify-center text-white font-medium">
                  {unread > 9 ? '9+' : unread}
                </span>
              )}
            </Button>

            {notifOpen && (
              <div className="absolute right-0 top-10 w-80 bg-card border rounded-lg shadow-lg z-50 overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b">
                  <span className="text-sm font-semibold">Recent Feedback</span>
                  {unread > 0 && (
                    <Badge variant="destructive" className="text-xs">{unread} negative</Badge>
                  )}
                </div>

                {recent.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-6">No feedback yet.</p>
                ) : (
                  <div className="divide-y max-h-72 overflow-y-auto">
                    {recent.map((entry, i) => (
                      <div key={i} className="flex items-start gap-3 px-4 py-3 hover:bg-accent/30 transition-colors">
                        <div className={`mt-0.5 shrink-0 ${entry.type === 'up' ? 'text-green-500' : 'text-red-500'}`}>
                          {entry.type === 'up'
                            ? <ThumbsUp className="h-3.5 w-3.5" />
                            : <ThumbsDown className="h-3.5 w-3.5" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs truncate">{entry.query || '(no query)'}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{fmtTime(entry.timestamp)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="px-4 py-2 border-t">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full text-xs justify-center gap-1"
                    onClick={() => { setNotifOpen(false); navigate('/admin'); }}
                  >
                    <ExternalLink className="h-3 w-3" />
                    View all in Admin Dashboard
                  </Button>
                </div>
              </div>
            )}
          </div>

          <Button variant="ghost" size="icon" onClick={onToggleTheme}>
            {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>

        </div>
      </div>
    </header>
  );
};

export default Header;
