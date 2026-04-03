import React, { useMemo, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Bot,
  User,
  ThumbsUp,
  ThumbsDown,
  Copy,
  ExternalLink,
  Map,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import CoverageMap, { detectRegions } from './CoverageMap';

interface MessageSource {
  satellite: string;
  dataset: string;
  timeRange: string;
  url?: string;
}

interface ChatMessageProps {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
  sources?: MessageSource[];
  onFeedback?: (messageId: string, type: 'up' | 'down') => void;
  isLoading?: boolean;
}

/** Minimal markdown: **bold**, bullet lists, numbered lists, newlines */
const renderMarkdown = (text: string) => {
  if (!text) return null;
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];
  let listType: 'ul' | 'ol' | null = null;

  const flushList = () => {
    if (listItems.length === 0) return;
    const Tag = listType === 'ol' ? 'ol' : 'ul';
    const className = listType === 'ol'
      ? 'list-decimal list-inside space-y-1 my-2'
      : 'list-disc list-inside space-y-1 my-2';
    elements.push(
      <Tag key={elements.length} className={className}>
        {listItems.map((item, i) => <li key={i}>{formatInline(item)}</li>)}
      </Tag>
    );
    listItems = [];
    listType = null;
  };

  const formatInline = (line: string): React.ReactNode => {
    // Bold: **text**
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  for (const line of lines) {
    const trimmed = line.trim();
    // Bullet list
    if (/^[-*]\s/.test(trimmed)) {
      if (listType !== 'ul') flushList();
      listType = 'ul';
      listItems.push(trimmed.replace(/^[-*]\s+/, ''));
      continue;
    }
    // Numbered list
    if (/^\d+[.)]\s/.test(trimmed)) {
      if (listType !== 'ol') flushList();
      listType = 'ol';
      listItems.push(trimmed.replace(/^\d+[.)]\s+/, ''));
      continue;
    }
    flushList();
    if (!trimmed) {
      elements.push(<br key={elements.length} />);
    } else {
      elements.push(
        <p key={elements.length} className="text-sm leading-relaxed mb-1">
          {formatInline(trimmed)}
        </p>
      );
    }
  }
  flushList();
  return elements;
};

const ChatMessage: React.FC<ChatMessageProps> = ({
  id,
  content,
  isBot,
  timestamp,
  sources,
  onFeedback,
  isLoading,
}) => {
  const [mapOpen, setMapOpen] = useState(false);

  const detectedRegions = useMemo(
    () => (isBot && !isLoading && content ? detectRegions(content) : []),
    [isBot, isLoading, content]
  );

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  if (isBot) {
    return (
      <div className="flex items-start gap-3 mb-6">
        <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white flex-shrink-0">
          <Bot className="h-4 w-4" />
        </div>

        <div className="flex-1 max-w-[80%]">
          <Card className="bg-card">
            <CardContent className="p-4">
              {isLoading && !content ? (
                <div className="flex items-center gap-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                  <span className="text-sm text-muted-foreground">Analyzing satellite data...</span>
                </div>
              ) : (
                <>
                  <div className="prose prose-sm max-w-none">
                    {renderMarkdown(content)}
                    {isLoading && (
                      <span className="inline-block w-2 h-4 bg-primary/60 animate-pulse ml-0.5" />
                    )}
                  </div>

                  {sources && sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <h4 className="text-xs font-medium text-muted-foreground mb-2">Data Sources</h4>
                      <div className="space-y-2">
                        {sources.map((source, index) => (
                          <div
                            key={index}
                            className="flex items-center gap-2 text-xs cursor-pointer hover:bg-accent/50 rounded p-1 -ml-1 transition-colors"
                            onClick={() => source.url && window.open(source.url, '_blank')}
                          >
                            <Badge variant="outline" className="shrink-0">{source.satellite}</Badge>
                            <span className="text-muted-foreground truncate">{source.dataset}</span>
                            {source.url && (
                              <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0 ml-auto" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {!isLoading && detectedRegions.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full flex items-center justify-between text-xs text-muted-foreground hover:text-foreground"
                        onClick={() => setMapOpen(o => !o)}
                      >
                        <span className="flex items-center gap-1.5">
                          <Map className="h-3.5 w-3.5" />
                          Coverage Map
                          <span className="text-primary font-medium">
                            ({detectedRegions.map(r => r.name).join(', ')})
                          </span>
                        </span>
                        {mapOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </Button>
                      {mapOpen && (
                        <div className="mt-2">
                          <CoverageMap regions={detectedRegions} />
                        </div>
                      )}
                    </div>
                  )}

                  {!isLoading && (
                    <div className="flex items-center justify-between mt-4 pt-3 border-t">
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={() => onFeedback?.(id, 'up')}>
                          <ThumbsUp className="h-3 w-3 mr-1" /> Helpful
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => onFeedback?.(id, 'down')}>
                          <ThumbsDown className="h-3 w-3 mr-1" /> Not helpful
                        </Button>
                      </div>
                      <Button variant="ghost" size="sm" onClick={handleCopy}>
                        <Copy className="h-3 w-3 mr-1" /> Copy
                      </Button>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          <p className="text-xs text-muted-foreground mt-1">
            {timestamp.toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 justify-end mb-6">
      <div className="max-w-[80%]">
        <Card className="bg-primary text-primary-foreground">
          <CardContent className="p-4">
            <p className="text-sm whitespace-pre-wrap">{content}</p>
          </CardContent>
        </Card>
        <p className="text-xs text-muted-foreground mt-1 text-right">
          {timestamp.toLocaleTimeString()}
        </p>
      </div>

      <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white flex-shrink-0">
        <User className="h-4 w-4" />
      </div>
    </div>
  );
};

export default ChatMessage;
