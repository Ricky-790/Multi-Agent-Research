import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { AppShell } from "../components/AppShell";
import { API_BASE_URL } from "../config";

interface ChatMessage {
  id: string;
  role: "User" | "Agent" | "ResearchEvent";
  content: string;
  sequenceNo: number;
  createdAt: Date;
  streaming?: boolean;
  reportId?: string;
}
interface ResearchEvent {
  reportId: string;
  title: string;
}
interface SseEnvelope {
  event: string;
  data: string;
}

const QUICK_SUGGESTIONS = [
  "Emerging Tech Trends",
  "Supply Chain Vulnerabilities",
  "BTC vs SOL vs ETH deep research",
];

export const ChatPage: React.FC = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const { conversationId: paramConversationId } = useParams<{
    conversationId: string;
  }>();

  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(
    paramConversationId ?? null,
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const abortRef = useRef<AbortController | null>(null);
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  // Sync param -> state when navigating between conversation URLs.
  useEffect(() => {
    setConversationId(paramConversationId ?? null);
    // Load messages when arriving on an existing conversation.
    if (!paramConversationId) {
      setMessages([]);
    } else {
      fetchConversationHistory(paramConversationId);
    }
  }, [paramConversationId]);

  // Auto-scroll to the latest message while streaming.
  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch conversation history from the backend when navigating to a conversation.
  const fetchConversationHistory = useCallback(async (conversationId: string) => {
    if (!token) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/chat/${conversationId}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (!res.ok) {
        console.error("Failed to fetch conversation history");
        return;
      }
      const data = await res.json();
      // Convert the backend format to our ChatMessage format.
      const history: ChatMessage[] = (data?.messages || []).map(
        (m: any) => ({
          id: m.message_id || m.id,
          role: m.role as "User" | "Agent",
          content: m.content || m.message_content,
          sequenceNo: m.sequence_no || m.sequenceNo,
          createdAt: new Date(m.created_at || m.createdAt),
        })
      );
      setMessages(history);
    } catch (err) {
      console.error("Error fetching conversation history:", err);
    }
  }, [token]);

  const cancelStream = useCallback(() => {
    if (abortRef.current) {
      try {
        abortRef.current.abort();
      } catch {
        /* noop */
      }
      abortRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => cancelStream();
  }, [cancelStream]);

  const submit = useCallback(
    async (text: string, activeConversationId: string | null) => {
      if (!text.trim() || !token) return;

      setError(null);
      setStreaming(true);
      cancelStream();

      const controller = new AbortController();
      abortRef.current = controller;

      // Optimistic user bubble — the server will confirm via user_message_created.
      const optimisticId = `tmp-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: optimisticId, role: "User", content: text.trim(), sequenceNo: 0, createdAt: new Date() },
      ]);
      setQuery("");

      try {
        const res = await fetch(`${API_BASE_URL}/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: text.trim(),
            conversation_id: activeConversationId || undefined,
          }),
          signal: controller.signal,
        });

        if (!res.ok || !res.body) {
          let detail = `Request failed with status ${res.status}`;
          try {
            const data = await res.json();
            if (data?.detail) detail = data.detail;
          } catch {
            /* not json */
          }
          throw new Error(detail);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // SSE messages are delimited by blank lines. Split out complete ones.
          let idx;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const rawEvent = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);

            // The backend uses FastAPI's EventSourceResponse which serializes
            // the event envelope into a single `data:` line. Collect any
            // `data:` lines (multi-line data is joined with newlines per spec).
            let dataStr = "";
            for (const line of rawEvent.split("\n")) {
              if (line.startsWith("data:")) {
                dataStr += (dataStr ? "\n" : "") + line.slice(5).trim();
              }
            }
            if (!dataStr) continue;

            // Try the wrapped-envelope format first:
            //   {"event": "<name>", "data": "<json-string>"}
            let envelope: SseEnvelope | null = null;
            let outer: any = null;
            try {
              outer = JSON.parse(dataStr);
            } catch {
              outer = null;
            }
            if (outer && typeof outer === "object" && outer.event) {
              envelope = outer as SseEnvelope;
            }

            const eventName = envelope?.event ?? "";
            let payload: any = null;
            if (envelope) {
              // Inner `data` is usually a JSON object (e.g. {"message_id":
              // "..."}) but may also be a JSON-encoded string in older event
              // types. Try object first, then string, otherwise leave null.
              const inner = envelope.data;
              if (inner && typeof inner === "object") {
                payload = inner;
              } else if (typeof inner === "string") {
                try {
                  payload = JSON.parse(inner);
                } catch {
                  payload = inner;
                }
              } else {
                payload = inner;
              }
            } else {
              payload = outer;
            }

            if (eventName === "conversation_created") {
              const newId = payload?.conversation_id;
              if (newId) {
                setConversationId(newId);
                // Don't navigate yet — the SSE reader is tied to this
                // component instance. React Router will unmount us mid-stream
                // if we navigate now, killing the response. We update the URL
                // *after* the `done` event in the `finally` block below.
              }
            } else if (eventName === "user_message_created") {
              // Replace the optimistic bubble with the server-confirmed one.
              setMessages((prev) => {
                const withoutOptimistic = prev.filter(
                  (m) => m.id !== optimisticId,
                );
                if (payload?.message_id || payload?.id) {
                  return [
                    ...withoutOptimistic,
                    {
                      id: payload.message_id ?? payload.id,
                      role: "User",
                      content: payload.content ?? text.trim(),
                      sequenceNo: payload.sequence_no ?? 0,
                      createdAt: payload.created_at ? new Date(payload.created_at) : new Date(),
                    },
                  ];
                }
                return withoutOptimistic;
              });
            } else if (eventName === "starting_response_stream") {
              // Ensure an assistant placeholder exists so deltas append to it.
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last && last.role === "Agent" && last.streaming) {
                  return prev;
                }
                return [
                  ...prev,
                  {
                    id: `stream-${Date.now()}`,
                    role: "Agent",
                    content: "",
                    streaming: true,
                    sequenceNo: 0,
                    createdAt: new Date(),
                  },
                ];
              });
            } else if (eventName === "message_delta") {
              // For deltas, payload may be a plain string (the agent's reply)
              // or an object with a `delta` field.
              const piece =
                typeof payload === "string"
                  ? payload
                  : (payload?.delta ?? payload?.response ?? "");
              if (!piece) continue;
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last && last.role === "Agent") {
                  next[next.length - 1] = {
                    ...last,
                    content: last.content + piece,
                    streaming: true,
                  };
                } else {
                  next.push({
                    id: `stream-${Date.now()}`,
                    role: "Agent",
                    content: piece,
                    streaming: true,
                    sequenceNo: 0,
                    createdAt: new Date(),
                  });
                }
                return next;
              });
            } else if (eventName === "message_complete") {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last && last.role === "Agent") {
                  next[next.length - 1] = {
                    id: payload?.message_id ?? payload?.id ?? last.id,
                    role: "Agent",
                    content: payload?.content ?? last.content,
                    streaming: false,
                    sequenceNo: payload?.sequence_no ?? last.sequenceNo ?? 0,
                    createdAt: payload?.created_at ? new Date(payload.created_at) : last.createdAt,
                  };
                } else if (payload) {
                  next.push({
                    id: payload.message_id ?? payload.id,
                    role: "Agent",
                    content: payload.content ?? "",
                    sequenceNo: payload.sequence_no ?? 0,
                    createdAt: payload.created_at ? new Date(payload.created_at) : new Date(),
                  });
                }
                return next;
              });
            } else if (eventName === "done") {
              setMessages((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last && last.role === "Agent" && last.streaming) {
                  next[next.length - 1] = { ...last, streaming: false };
                }
                return next;
              });
            } else if (eventName === "Starting a research") {
              const reportData = payload as { report_id: string; title: string };
              setMessages((prev) => [
                ...prev,
                {
                  id: `research-${Date.now()}`,
                  role: "ResearchEvent",
                  content: "Starting research",
                  sequenceNo: 0,
                  createdAt: new Date(),
                  reportId: reportData?.report_id,
                },
              ]);
            }
          }
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          // User cancelled — quietly drop the optimistic bubble if nothing
          // was confirmed.
          setMessages((prev) => prev.filter((m) => m.id !== optimisticId));
          return;
        }
        setError((err as Error).message || "Failed to send query.");
        setMessages((prev) => prev.filter((m) => m.id !== optimisticId));
      } finally {
        setStreaming(false);
        if (abortRef.current === controller) abortRef.current = null;

        // Navigate AFTER the stream ends so React Router doesn't unmount us
        // mid-stream (which would abort the fetch and drop the messages).
        // Use the live `conversationId` from state so we don't capture a stale
        // value via the closure.
        setConversationId((currentId) => {
          if (currentId && currentId !== paramConversationId) {
            // Defer the navigation so it happens after this state update
            // commits and the SSE reader has fully released the response.
            queueMicrotask(() => {
              navigate(`/chat/${currentId}`, { replace: true });
            });
          }
          return currentId;
        });
      }
    },
    [token, cancelStream, navigate, paramConversationId],
  );

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submit(query, conversationId);
  };

  const onSuggestion = (s: string) => {
    submit(s, conversationId);
  };

  // Empty state — show the centered "What should Spectator look into?" prompt.
  // Otherwise show the conversation scrollback + the input pinned at the bottom.
  const isEmpty = messages.length === 0;

  return (
    <AppShell>
      <div className="relative flex flex-col h-full min-h-full">
        {/* Conversation scroll area */}
        {!isEmpty && (
          <div
            ref={scrollerRef}
            className="flex-1 overflow-y-auto px-margin-mobile md:px-margin-desktop py-8"
          >
            <div className="max-w-3xl mx-auto flex flex-col gap-6">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} navigate={navigate} />
              ))}
              {streaming && (
                <div className="self-start flex items-center gap-2 text-on-surface-variant opacity-60">
                  <span className="material-symbols-outlined text-[16px] animate-status-pulse">
                    sync
                  </span>
                  <span className="font-label-sm text-label-sm">
                    Spectator is thinking…
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty state hero */}
        {isEmpty && (
          <div className="flex-1 flex flex-col justify-center items-center px-margin-mobile md:px-margin-desktop pt-12 pb-8">
            <div className="w-full max-w-3xl flex flex-col items-center gap-12">
              <h2 className="font-display-lg text-display-lg text-on-surface text-center opacity-90 tracking-tight">
                What should Spectator look into?
              </h2>

              {error && (
                <div
                  role="alert"
                  className="w-full font-body-md text-body-md text-error border border-error-container bg-surface-container-low rounded px-4 py-3"
                >
                  {error}
                </div>
              )}

              <form
                onSubmit={onSubmit}
                className="w-full relative"
                autoComplete="off"
              >
                <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                  <span className="material-symbols-outlined text-outline text-[24px]">
                    temp_preferences_custom
                  </span>
                </div>
                <input
                  className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-5 pl-16 pr-16 text-body-lg text-on-surface placeholder:text-outline-variant focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary focus:bg-surface transition-all duration-300"
                  placeholder="Enter a company, market sector, or geopolitical entity..."
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={streaming}
                />
                <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                  <button
                    type="submit"
                    disabled={streaming || !query.trim()}
                    className="p-2 rounded text-outline hover:text-primary hover:bg-surface-container-high transition-colors duration-200 flex items-center justify-center disabled:opacity-50"
                    aria-label="Send"
                  >
                    <span className="material-symbols-outlined text-[24px]">
                      send
                    </span>
                  </button>
                </div>
              </form>

              <div className="flex flex-wrap justify-center gap-3 mt-4">
                {QUICK_SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => onSuggestion(s)}
                    disabled={streaming}
                    className="px-4 py-2 border border-outline-variant rounded-full text-label-sm font-label-sm text-on-surface-variant hover:border-outline hover:text-on-surface transition-colors bg-surface-container-lowest disabled:opacity-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Pinned composer when there's existing conversation scrollback. */}
        {!isEmpty && (
          <div className="border-t border-outline-variant bg-background px-margin-mobile md:px-margin-desktop py-4">
            <form
              onSubmit={onSubmit}
              className="max-w-3xl mx-auto w-full relative"
              autoComplete="off"
            >
              {error && (
                <div
                  role="alert"
                  className="mb-3 font-body-md text-body-md text-error border border-error-container bg-surface-container-low rounded px-3 py-2"
                >
                  {error}
                </div>
              )}
              <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                <span className="material-symbols-outlined text-outline text-[24px]">
                  temp_preferences_custom
                </span>
              </div>
              <input
                className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-4 pl-16 pr-16 text-body-md text-on-surface placeholder:text-outline-variant focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary focus:bg-surface transition-all duration-200"
                placeholder="Ask Spectator anything…"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={streaming}
              />
              <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                <button
                  type="submit"
                  disabled={streaming || !query.trim()}
                  className="p-2 rounded text-outline hover:text-primary hover:bg-surface-container-high transition-colors duration-200 flex items-center justify-center disabled:opacity-50"
                  aria-label="Send"
                >
                  <span className="material-symbols-outlined text-[24px]">
                    send
                  </span>
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </AppShell>
  );
};

const MessageBubble: React.FC<{ message: ChatMessage; navigate: (to: string) => void }> = ({ message, navigate }) => {
  const isUser = message.role === "User";
  const isResearchEvent = message.role === "ResearchEvent";

  if (isResearchEvent) {
    return (
      <div className="flex justify-start">
        <div
          className="max-w-[85%] rounded-lg px-4 py-3 font-body-md text-body-md bg-surface-container-low border border-outline-variant text-on-surface cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => message.reportId && navigate(`/report/${message.reportId}`)}
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-[18px]">description</span>
            <span className="font-medium">Starting research</span>
          </div>
          {message.reportId && (
            <p className="text-xs text-on-surface-variant mt-1">
              Report ID: {message.reportId}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-5 py-3 font-body-md text-body-md ${
          isUser
            ? "bg-primary-container text-on-primary-container"
            : "bg-surface-container-low border border-outline-variant text-on-surface"
        }`}
      >
        {message.content || (
          <span className="inline-block w-2 h-2 rounded-full bg-primary animate-status-pulse" />
        )}
      </div>
    </div>
  );
};
