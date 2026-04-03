import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Trash2, Download } from 'lucide-react';
import ChatInput from '@/components/query/ChatInput';
import ChatMessage from '@/components/query/ChatMessage';
import ChatWelcome from '@/components/query/ChatWelcome';
import jsPDF from 'jspdf';

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

    const botId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Add placeholder bot message for streaming
    setMessages(prev => [...prev, {
      id: botId, content: '', isBot: true, timestamp: new Date(), sources: []
    }]);

    try {
      const response = await fetch('/api/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          history: messages.slice(-6).map(m => ({ content: m.content, isBot: m.isBot })),
        }),
      });

      if (!response.ok) throw new Error(`Request failed with status ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No response body');

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'sources') {
              setMessages(prev => prev.map(m =>
                m.id === botId ? { ...m, sources: event.sources } : m
              ));
            } else if (event.type === 'token') {
              setMessages(prev => prev.map(m =>
                m.id === botId ? { ...m, content: m.content + event.content } : m
              ));
            }
          } catch { /* skip malformed lines */ }
        }
      }
    } catch (error) {
      console.error('API call failed:', error);
      // If streaming failed, update the placeholder with error
      setMessages(prev => prev.map(m =>
        m.id === botId
          ? { ...m, content: error instanceof Error ? error.message : 'Request failed' }
          : m
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleTemplateSelect = (template: string) => {
    handleSendMessage(template);
  };

  const handleExportPDF = () => {
    const doc = new jsPDF({ unit: 'pt', format: 'a4' });
    const pageW = doc.internal.pageSize.getWidth();
    const margin = 40;
    const maxW = pageW - margin * 2;
    let y = margin;

    const addPage = () => {
      doc.addPage();
      y = margin;
    };

    const checkY = (needed: number) => {
      if (y + needed > doc.internal.pageSize.getHeight() - margin) addPage();
    };

    // Header
    doc.setFillColor(15, 23, 42);
    doc.rect(0, 0, pageW, 56, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('SatSage — Chat Export', margin, 36);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(180, 200, 220);
    doc.text(new Date().toLocaleString(), pageW - margin, 36, { align: 'right' });
    y = 72;

    const completedMessages = messages.filter(m => m.content.trim());

    completedMessages.forEach((msg, idx) => {
      const label = msg.isBot ? 'MOSDAC Bot' : 'You';
      const time = msg.timestamp.toLocaleTimeString();
      const isBot = msg.isBot;

      checkY(32);

      // Label row
      doc.setFontSize(8);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(isBot ? 56 : 99, isBot ? 189 : 102, isBot ? 248 : 241);
      doc.text(`${label}  ·  ${time}`, margin, y);
      y += 14;

      // Message body
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(10);
      doc.setTextColor(30, 30, 30);

      // Strip markdown bold markers for plain text
      const plainText = msg.content.replace(/\*\*([^*]+)\*\*/g, '$1');
      const lines = doc.splitTextToSize(plainText, maxW);
      lines.forEach((line: string) => {
        checkY(14);
        doc.text(line, margin, y);
        y += 14;
      });

      // Sources
      if (isBot && msg.sources && msg.sources.length > 0) {
        checkY(14);
        doc.setFontSize(8);
        doc.setTextColor(120, 120, 140);
        doc.setFont('helvetica', 'italic');
        const srcText = 'Sources: ' + msg.sources.map(s => `${s.satellite} — ${s.dataset.slice(0, 60)}`).join(' | ');
        const srcLines = doc.splitTextToSize(srcText, maxW);
        srcLines.forEach((line: string) => {
          checkY(12);
          doc.text(line, margin, y);
          y += 12;
        });
      }

      // Separator (except last)
      if (idx < completedMessages.length - 1) {
        y += 6;
        checkY(2);
        doc.setDrawColor(220, 220, 230);
        doc.line(margin, y, pageW - margin, y);
        y += 10;
      }
    });

    // Footer on last page
    const totalPages = (doc as any).internal.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
      doc.setPage(p);
      doc.setFontSize(8);
      doc.setTextColor(160, 160, 170);
      doc.setFont('helvetica', 'normal');
      doc.text(`SatSage  ·  mosdac.gov.in  ·  Page ${p} of ${totalPages}`, pageW / 2, doc.internal.pageSize.getHeight() - 20, { align: 'center' });
    }

    const filename = `mosdac-chat-${new Date().toISOString().slice(0, 10)}.pdf`;
    doc.save(filename);
  };

  const handleFeedback = (messageId: string, type: 'up' | 'down') => {
    const msg = messages.find(m => m.id === messageId);
    const prevMsg = messages[messages.indexOf(msg!) - 1];
    fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messageId,
        query: prevMsg?.content || '',
        response: msg?.content || '',
        type,
      }),
    }).catch(() => {});
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
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="sm" onClick={handleExportPDF}>
                      <Download className="h-3 w-3 mr-1" />
                      Export PDF
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => setMessages([])}>
                      <Trash2 className="h-3 w-3 mr-1" />
                      Clear History
                    </Button>
                  </div>
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
