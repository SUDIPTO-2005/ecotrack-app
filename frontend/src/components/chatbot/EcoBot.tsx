import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { apiClient } from '../../api/apiClient';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const WELCOME_MSG: ChatMessage = {
  role: 'assistant',
  content: "👋 Hi! I'm **EcoBot**, your AI carbon coach. Ask me anything about reducing your footprint — transport, energy, diet, or offsets!",
  timestamp: new Date(),
};

const SUGGESTIONS = [
  "How can I reduce my transport emissions?",
  "What diet has the lowest carbon footprint?",
  "Explain carbon offsets simply",
  "How much CO2 does flying produce?",
];

export default function EcoBot() {
  const { isAuthenticated } = useAppStore();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MSG]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pulsing, setPulsing] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' });
      setPulsing(false);
    }
  }, [messages, open]);

  if (!isAuthenticated) return null;

  const sendMessage = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    const userMsg: ChatMessage = { role: 'user', content: msg, timestamp: new Date() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const history = newMessages.slice(-6).map(m => ({ role: m.role, content: m.content }));
      const resp = await apiClient.request<{ reply: string; was_fallback: boolean }>('/ai-coach/chat/', {
        method: 'POST',
        body: JSON.stringify({ message: msg, history }),
      });
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: resp.reply,
        timestamp: new Date(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I couldn't connect. Check your internet connection and try again.",
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatContent = (text: string) => {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  return (
    <div className="ecobot-wrapper">
      {/* Chat Panel */}
      {open && (
        <div className="ecobot-panel">
          {/* Header */}
          <div className="ecobot-header">
            <div className="ecobot-header-info">
              <div className="ecobot-avatar">🌿</div>
              <div>
                <p className="ecobot-name">EcoBot</p>
                <p className="ecobot-status">
                  <span className="status-dot"></span> Online
                </p>
              </div>
            </div>
            <button 
              className="ecobot-close" 
              onClick={() => setOpen(false)}
              aria-label="Close EcoBot Chat"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="ecobot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble-row ${msg.role}`}>
                {msg.role === 'assistant' && <div className="bot-avatar-sm">🌿</div>}
                <div className={`chat-bubble ${msg.role}`}>
                  <p
                    dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
                  />
                  <span className="chat-time">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-bubble-row assistant">
                <div className="bot-avatar-sm">🌿</div>
                <div className="chat-bubble assistant typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Suggestions */}
          {messages.length <= 1 && (
            <div className="ecobot-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => sendMessage(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="ecobot-input-row">
            <textarea
              className="ecobot-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask EcoBot anything..."
              rows={1}
              disabled={loading}
              aria-label="Ask EcoBot anything..."
            />
            <button
              className="ecobot-send"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              aria-label="Send message to EcoBot"
            >
              ➤
            </button>
          </div>
        </div>
      )}

      {/* Floating Trigger Button */}
      <button
        className={`ecobot-fab ${pulsing ? 'fab-pulse' : ''}`}
        onClick={() => setOpen(o => !o)}
        title="Chat with EcoBot"
        aria-expanded={open}
        aria-label={open ? "Close EcoBot chat" : "Open EcoBot chat"}
      >
        {open ? '✕' : '🌿'}
        {!open && <span className="fab-label">EcoBot</span>}
      </button>
    </div>
  );
}
