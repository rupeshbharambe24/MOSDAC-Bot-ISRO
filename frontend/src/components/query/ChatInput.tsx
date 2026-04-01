import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Satellite, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading, disabled }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const characterLimit = 2000;
  const charactersUsed = input.length;

  const handleSend = () => {
    if (input.trim() && !isLoading && !disabled) {
      onSendMessage(input.trim());
      setInput('');
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t bg-card/50 backdrop-blur p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about satellite data, weather patterns, ocean monitoring..."
              className="min-h-[60px] max-h-32 resize-none pr-16"
              disabled={isLoading || disabled}
              maxLength={characterLimit}
              autoFocus
            />

            <div className="absolute bottom-2 right-2">
              <span className="text-xs text-muted-foreground">
                {charactersUsed}/{characterLimit}
              </span>
            </div>
          </div>

          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading || disabled}
            className="gradient-primary text-white hover:opacity-90 h-[60px] px-6"
            aria-label="Send message"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Satellite className="h-5 w-5" />
            )}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send, Shift+Enter for new line.
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
