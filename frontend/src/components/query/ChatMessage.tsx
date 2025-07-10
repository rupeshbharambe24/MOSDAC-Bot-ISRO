
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Bot, 
  User, 
  ThumbsUp, 
  ThumbsDown, 
  Copy, 
  Download,
  ExternalLink 
} from 'lucide-react';

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

const ChatMessage: React.FC<ChatMessageProps> = ({
  id,
  content,
  isBot,
  timestamp,
  sources,
  onFeedback,
  isLoading
}) => {
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
              {isLoading ? (
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
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
                  </div>
                  
                  {sources && sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <h4 className="text-xs font-medium text-muted-foreground mb-2">Data Sources</h4>
                      <div className="space-y-2">
                        {sources.map((source, index) => (
                          <div key={index} className="flex items-center gap-2 text-xs">
                            <Badge variant="outline">{source.satellite}</Badge>
                            <span className="text-muted-foreground">{source.dataset}</span>
                            <span className="text-muted-foreground">•</span>
                            <span className="text-muted-foreground">{source.timeRange}</span>
                            {source.url && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-4 w-4 p-0 ml-auto"
                                onClick={() => window.open(source.url, '_blank')}
                                aria-label="View source"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between mt-4 pt-3 border-t">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onFeedback?.(id, 'up')}
                        aria-label="Helpful"
                      >
                        <ThumbsUp className="h-3 w-3 mr-1" />
                        Helpful
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onFeedback?.(id, 'down')}
                        aria-label="Not helpful"
                      >
                        <ThumbsDown className="h-3 w-3 mr-1" />
                        Not helpful
                      </Button>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCopy}
                        aria-label="Copy response"
                      >
                        <Copy className="h-3 w-3 mr-1" />
                        Copy
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label="Export data"
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Export
                      </Button>
                    </div>
                  </div>
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
