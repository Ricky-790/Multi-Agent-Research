import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Send, Loader2, Sparkles, Bot, AlertCircle } from "lucide-react";

interface ChatPageProps {
  onNavigate: (path: string) => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({ onNavigate }) => {
  const { api } = useAuth();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [replyMessage, setReplyMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setReplyMessage(null);
    setError(null);

    try {
      const res = await api.post("/chat", { query: query.trim() });
      const data = res.data;

      if (data.report_id) {
        onNavigate(`/report/${data.report_id}`);
      } else {
        setReplyMessage(data.message || "No message returned.");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || err.message || "An error occurred while submitting your request.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-content">
        <div className="chat-header">
          <div className="chat-icon-glow">
            <Sparkles size={28} />
          </div>
          <h2>What would you like to research today?</h2>
          <p>Ask a question or provide a detailed topic to launch an autonomous multi-agent research workflow.</p>
        </div>

        {error && (
          <div className="error-banner">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {replyMessage && (
          <div className="chat-reply-card">
            <div className="reply-avatar">
              <Bot size={20} />
            </div>
            <div className="reply-body">
              <span className="reply-author">Assistant</span>
              <p>{replyMessage}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="chat-input-form">
          <div className="chat-input-wrapper">
            <textarea
              className="chat-textarea"
              placeholder="e.g. Analyze the market trends in solid state battery technology for 2026..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              disabled={loading}
              rows={3}
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={loading || !query.trim()}
              title="Submit Research Request"
            >
              {loading ? <Loader2 className="spinner" size={20} /> : <Send size={20} />}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
