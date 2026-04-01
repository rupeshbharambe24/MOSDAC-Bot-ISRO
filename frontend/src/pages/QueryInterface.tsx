import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Trash2 } from 'lucide-react';
import ChatInput from '@/components/query/ChatInput';
import ChatMessage from '@/components/query/ChatMessage';
import ChatWelcome from '@/components/query/ChatWelcome';

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
  sources?: {
    satellite: string;
    dataset: string;
    timeRange: string;
    url?: string;
  }[];
}

const STORAGE_KEY = 'mosdac-chat-history';

const saveMessages = (msgs: Message[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs));
  } catch { /* ignore quota errors */ }
};

const loadMessages = (): Message[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    return parsed.map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) }));
  } catch { return []; }
};

const QueryInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>(() => loadMessages());
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  // Handle sidebar template selection or "New Query" via navigation state
  useEffect(() => {
    const state = location.state as { initialQuery?: string; clearChat?: boolean } | null;
    if (!state) return;

    if (state.clearChat) {
      setMessages([]);
    }
    if (state.initialQuery) {
      handleSendMessage(state.initialQuery);
    }

    // Clear the state so refreshing doesn't re-trigger
    window.history.replaceState({}, document.title);
  }, [location.state]);

  const handleSendMessage = async (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          history: messages.slice(-6).map(m => ({ content: m.content, isBot: m.isBot })),
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        isBot: true,
        timestamp: new Date(),
        sources: data.sources || []
      };

      setMessages(prev => [...prev, botResponse]);
    } catch (error) {
      console.error('API call failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: error instanceof Error ? error.message : 'Request failed',
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTemplateSelect = (template: string) => {
    handleSendMessage(template);
  };

  const handleFeedback = (messageId: string, type: 'up' | 'down') => {
    console.log('Feedback:', messageId, type);
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="max-w-4xl mx-auto px-6 py-6">
            {messages.length === 0 ? (
              <ChatWelcome onTemplateSelect={handleTemplateSelect} />
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs text-muted-foreground">{messages.length} messages</span>
                  <Button variant="ghost" size="sm" onClick={() => setMessages([])}>
                    <Trash2 className="h-3 w-3 mr-1" />
                    Clear History
                  </Button>
                </div>
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    id={message.id}
                    content={message.content}
                    isBot={message.isBot}
                    timestamp={message.timestamp}
                    sources={message.sources}
                    onFeedback={handleFeedback}
                  />
                ))}

                {isLoading && (
                  <ChatMessage
                    id="loading"
                    content=""
                    isBot={true}
                    timestamp={new Date()}
                    isLoading={true}
                  />
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </ScrollArea>
      </div>

      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
};

export default QueryInterface;
