
import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Send, 
  Loader2, 
  Download, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  BarChart3,
  Map,
  FileText,
  Bot,
  User,
  Satellite
} from 'lucide-react';
import { QueryResponse } from '@/types/satellite';

interface ChatInterfaceProps {
  responses: QueryResponse[];
  onSendQuery: (query: string) => void;
  isLoading: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  responses, 
  onSendQuery, 
  isLoading 
}) => {
  const [query, setQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [responses]);

  const handleSend = () => {
    if (query.trim() && !isLoading) {
      onSendQuery(query);
      setQuery('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {responses.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <div className="relative">
              <div className="w-20 h-20 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
                <Satellite className="h-10 w-10 text-white" />
              </div>
              <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Welcome to ISRO SatQuery</h3>
              <p className="text-muted-foreground max-w-md">
                Ask me anything about satellite data, Earth observations, or space missions. 
                I can help you analyze oceanographic data, track weather patterns, and more.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 max-w-lg">
              <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white transition-colors">
                "Show SST data for Arabian Sea"
              </Badge>
              <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white transition-colors">
                "Track cyclone patterns"
              </Badge>
              <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white transition-colors">
                "Land use changes in Karnataka"
              </Badge>
            </div>
          </div>
        ) : (
          responses.map((response) => (
            <div key={response.id} className="space-y-4">
              {/* User Query */}
              <div className="flex items-start gap-3 justify-end">
                <div className="max-w-[80%]">
                  <Card className="bg-primary text-primary-foreground">
                    <CardContent className="p-4">
                      <p className="text-sm">{response.query}</p>
                    </CardContent>
                  </Card>
                  <p className="text-xs text-muted-foreground mt-1 text-right">
                    {new Date(response.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white">
                  <User className="h-4 w-4" />
                </div>
              </div>

              {/* Bot Response */}
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex-1 max-w-[80%]">
                  <Card className="bg-card">
                    <CardContent className="p-0">
                      <Tabs defaultValue="text" className="w-full">
                        <div className="p-4 pb-0">
                          <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="text" className="flex items-center gap-2">
                              <FileText className="h-4 w-4" />
                              Text
                            </TabsTrigger>
                            <TabsTrigger value="chart" className="flex items-center gap-2">
                              <BarChart3 className="h-4 w-4" />
                              Charts
                            </TabsTrigger>
                            <TabsTrigger value="map" className="flex items-center gap-2">
                              <Map className="h-4 w-4" />
                              Map
                            </TabsTrigger>
                          </TabsList>
                        </div>

                        <TabsContent value="text" className="p-4 pt-4">
                          <div className="prose prose-sm max-w-none">
                            <p className="text-sm leading-relaxed">{response.response.text}</p>
                          </div>
                          
                          {/* Sources */}
                          {response.response.sources && (
                            <div className="mt-4 pt-4 border-t">
                              <h4 className="text-xs font-medium text-muted-foreground mb-2">Data Sources</h4>
                              <div className="space-y-2">
                                {response.response.sources.map((source, index) => (
                                  <div key={index} className="flex items-center gap-2 text-xs">
                                    <Badge variant="outline">{source.satellite}</Badge>
                                    <span className="text-muted-foreground">{source.dataset}</span>
                                    <span className="text-muted-foreground">•</span>
                                    <span className="text-muted-foreground">{source.timeRange}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </TabsContent>

                        <TabsContent value="chart" className="p-4 pt-4">
                          <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                            <div className="text-center space-y-2">
                              <BarChart3 className="h-8 w-8 mx-auto text-muted-foreground" />
                              <p className="text-sm text-muted-foreground">Chart visualization would appear here</p>
                            </div>
                          </div>
                        </TabsContent>

                        <TabsContent value="map" className="p-4 pt-4">
                          <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                            <div className="text-center space-y-2">
                              <Map className="h-8 w-8 mx-auto text-muted-foreground" />
                              <p className="text-sm text-muted-foreground">Interactive map would appear here</p>
                            </div>
                          </div>
                        </TabsContent>
                      </Tabs>

                      {/* Action Buttons */}
                      <div className="p-4 pt-0 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <ThumbsUp className="h-3 w-3 mr-1" />
                            Helpful
                          </Button>
                          <Button variant="ghost" size="sm">
                            <ThumbsDown className="h-3 w-3 mr-1" />
                            Not helpful
                          </Button>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <Copy className="h-3 w-3 mr-1" />
                            Copy
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Download className="h-3 w-3 mr-1" />
                            Export
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(response.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
        
        {/* Loading Message */}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white">
              <Bot className="h-4 w-4" />
            </div>
            <Card className="bg-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Analyzing satellite data...</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-card/50 p-4">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about satellite data, weather patterns, ocean monitoring..."
              className="min-h-[40px] resize-none"
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
          <Button 
            onClick={handleSend}
            disabled={!query.trim() || isLoading}
            className="gradient-primary text-white hover:opacity-90"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
