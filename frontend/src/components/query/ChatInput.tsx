
import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Paperclip, Satellite, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string, file?: File) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading, disabled }) => {
  const [input, setInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const characterLimit = 2000;
  const charactersUsed = input.length;

  const handleSend = () => {
    if (input.trim() && !isLoading && !disabled) {
      onSendMessage(input.trim(), selectedFile || undefined);
      setInput('');
      setSelectedFile(null);
      textareaRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && (file.type === 'text/csv' || file.type === 'application/json')) {
      setSelectedFile(file);
    }
  };

  return (
    <div className="border-t bg-card/50 backdrop-blur p-4">
      <div className="max-w-4xl mx-auto">
        {selectedFile && (
          <div className="mb-2 p-2 bg-muted rounded-md flex items-center justify-between">
            <span className="text-sm">{selectedFile.name}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedFile(null)}
              className="h-6 w-6 p-0"
            >
              ×
            </Button>
          </div>
        )}
        
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about satellite data, weather patterns, ocean monitoring..."
              className="min-h-[60px] max-h-32 resize-none pr-16"
              disabled={isLoading || disabled}
              maxLength={characterLimit}
              autoFocus
            />
            
            <div className="absolute bottom-2 right-2 flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {charactersUsed}/{characterLimit}
              </span>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="h-8 w-8 p-0"
                disabled={isLoading || disabled}
                aria-label="Attach file"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
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
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send, Shift+Enter for new line. Attach CSV/JSON files for data analysis.
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
