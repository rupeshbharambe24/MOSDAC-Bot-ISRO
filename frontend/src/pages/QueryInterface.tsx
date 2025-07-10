import React, { useState, useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
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

const QueryInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

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
    const response = await fetch('/api/query', {  // Will be proxied to FastAPI
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`)
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
    // Implement feedback API call here
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Chat Messages Area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="max-w-4xl mx-auto px-6 py-6">
            {messages.length === 0 ? (
              <ChatWelcome onTemplateSelect={handleTemplateSelect} />
            ) : (
              <>
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

      {/* Chat Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
};

export default QueryInterface;