import { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Send,
  Loader2,
  MessageSquare,
  Bot,
  User,
  FileText,
} from 'lucide-react';
import { getContract, chatWithContract, type ChatMessage } from '../lib/api';
import { cn } from '../lib/utils';

export function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: contract } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => getContract(id!),
    enabled: !!id,
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const suggestedQuestions = [
    'What are the termination conditions?',
    'Is the indemnity capped?',
    'Who carries the most risk?',
    'What is the governing law?',
    'Summarize the payment terms.',
    'Are there any non-compete clauses?',
  ];

  const handleSend = async (message: string) => {
    if (!message.trim() || !id) return;

    const userMsg: ChatMessage = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatWithContract(id, message);
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: response.response,
        citations: response.citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  return (
    <div className="flex flex-col h-full animate-fade-in">
      {/* Header */}
      <div className="px-8 py-4 border-b border-[var(--color-border)] flex items-center gap-4 shrink-0">
        <Link
          to={`/contracts/${id}`}
          className="p-2 rounded-lg hover:bg-[var(--color-secondary)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-[var(--color-primary)]" />
          <div>
            <h1 className="text-lg font-semibold text-[var(--color-foreground)]">
              Contract Chat
            </h1>
            <p className="text-xs text-[var(--color-muted-foreground)]">
              {contract?.filename || 'Loading...'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-[var(--color-primary)]/10 flex items-center justify-center mb-4">
              <Bot className="h-8 w-8 text-[var(--color-primary)]" />
            </div>
            <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-2">
              Ask about this contract
            </h2>
            <p className="text-sm text-[var(--color-muted-foreground)] mb-6 max-w-md">
              I have analyzed the entire contract. Ask me anything about its terms,
              clauses, risks, or obligations.
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-lg">
              {suggestedQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="text-left px-3 py-2 rounded-lg text-xs text-[var(--color-muted-foreground)] bg-[var(--color-secondary)] hover:bg-[var(--color-accent)] hover:text-[var(--color-foreground)] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              'flex gap-3 max-w-3xl',
              msg.role === 'user' ? 'ml-auto flex-row-reverse' : '',
            )}
          >
            <div
              className={cn(
                'w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
                msg.role === 'user'
                  ? 'bg-[var(--color-primary)]'
                  : 'bg-[var(--color-secondary)]',
              )}
            >
              {msg.role === 'user' ? (
                <User className="h-4 w-4 text-white" />
              ) : (
                <Bot className="h-4 w-4 text-[var(--color-primary)]" />
              )}
            </div>
            <div
              className={cn(
                'rounded-xl px-4 py-3 max-w-[80%]',
                msg.role === 'user'
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'glass-card',
              )}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-[var(--color-border)] space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)]">
                    Citations
                  </p>
                  {msg.citations.map((cite, j) => (
                    <div
                      key={j}
                      className="flex items-start gap-2 text-xs text-[var(--color-muted-foreground)]"
                    >
                      <FileText className="h-3 w-3 mt-0.5 shrink-0" />
                      <span>
                        <strong>Section {cite.section_number}:</strong> {cite.snippet}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-lg bg-[var(--color-secondary)] flex items-center justify-center">
              <Bot className="h-4 w-4 text-[var(--color-primary)]" />
            </div>
            <div className="glass-card rounded-xl px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin text-[var(--color-primary)]" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-8 py-4 border-t border-[var(--color-border)] shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-3 max-w-3xl mx-auto">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about this contract..."
            disabled={isLoading}
            className="flex-1 bg-[var(--color-secondary)] border border-[var(--color-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-foreground)] placeholder:text-[var(--color-muted-foreground)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={cn(
              'px-4 rounded-xl transition-all flex items-center justify-center',
              input.trim() && !isLoading
                ? 'bg-[var(--color-primary)] text-white hover:opacity-90'
                : 'bg-[var(--color-secondary)] text-[var(--color-muted-foreground)] cursor-not-allowed',
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
