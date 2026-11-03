/**
 * AI Assistant Page
 * Interactive conversational interface powered by Google Gemini and validated backend tools.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  User,
  Send,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Wrench,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Loader2,
  HelpCircle,
} from 'lucide-react';

import { agentApi } from '../services/api';
import type { AgentStatusData, ToolExecutionMeta } from '../types';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools_called?: ToolExecutionMeta[];
  timestamp: string;
}

const SUGGESTED_PROMPTS = [
  'What ingredients are running low?',
  'Which ingredients are consumed most frequently?',
  'Analyze my current inventory.',
  'What ingredients are approaching expiration?',
  'Which menu items have the highest food costs?',
  'Generate a procurement recommendation.',
  'Summarize restaurant performance.',
];

export function AiAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hello! I am your **RestaurantOps AI Assistant**, powered by Google Gemini.\n\nI can analyze your pantry inventory, track consumption velocity, identify expiration risks, evaluate dish profitability, and generate replenishment purchase plans.\n\nHow can I help your kitchen today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<AgentStatusData | null>(null);
  const [showConfigHelp, setShowConfigHelp] = useState<boolean>(false);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check agent configuration status on mount
  useEffect(() => {
    async function checkStatus() {
      const res = await agentApi.getStatus();
      if (res.success) {
        setStatus(res.data);
        if (!res.data.is_configured) {
          setShowConfigHelp(true);
        }
      }
    }
    checkStatus();
  }, []);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const historyPayload = messages
        .filter((m) => m.id !== 'welcome')
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await agentApi.chat({
        message: text,
        history: historyPayload,
      });

      if (res.success) {
        const assistantMsg: Message = {
          id: `bot-${Date.now()}`,
          role: 'assistant',
          content: res.data.response,
          tools_called: res.data.tools_called,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        const errorMsg: Message = {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Request failed: ${res.error}${res.detail ? ` (${res.detail})` : ''}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    } catch (err) {
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Network error: ${err instanceof Error ? err.message : 'Failed to reach backend'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: 'welcome-reset',
        role: 'assistant',
        content: "Conversation cleared. What would you like to investigate next?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const toggleTools = (msgId: string) => {
    setExpandedTools((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] max-w-5xl mx-auto space-y-3">

      {/* ── Header & Status Bar ──────────────────────────────────── */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-600 text-white">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">AI Assistant</h2>
              {status?.is_configured ? (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  Gemini Ready ({status.model})
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                  <AlertCircle className="w-3 h-3 text-amber-600" />
                  API Key Needed
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Natural language queries backed by validated backend database tools.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          {!status?.is_configured && (
            <button
              onClick={() => setShowConfigHelp((v) => !v)}
              className="flex items-center gap-1 text-xs text-amber-800 bg-amber-50 border border-amber-200 hover:bg-amber-100 px-2.5 py-1.5 rounded-lg font-medium transition-colors"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Setup Guide</span>
            </button>
          )}

          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-50 border border-slate-200 hover:bg-slate-100 px-3 py-1.5 rounded-lg font-medium transition-colors"
            title="Reset conversation"
          >
            <Trash2 className="w-3.5 h-3.5 text-slate-500" />
            <span>Clear Chat</span>
          </button>
        </div>
      </div>

      {/* ── Unconfigured Setup Banner (Collapsible) ───────────────── */}
      {showConfigHelp && !status?.is_configured && (
        <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 shadow-sm shrink-0">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1.5">
                <p className="font-bold text-amber-950">How to Activate the Gemini AI Assistant:</p>
                <ol className="list-decimal list-inside space-y-1 text-amber-900/90 leading-relaxed">
                  <li>
                    Open your backend configuration file at{' '}
                    <code className="bg-amber-100/70 px-1 py-0.5 rounded font-mono text-amber-950">
                      backend/.env
                    </code>
                  </li>
                  <li>
                    Locate line 23:{' '}
                    <code className="bg-amber-100/70 px-1 py-0.5 rounded font-mono text-amber-950">
                      GEMINI_API_KEY=your_gemini_api_key_here
                    </code>
                  </li>
                  <li>
                    Replace the placeholder with your Gemini API key from{' '}
                    <a
                      href="https://aistudio.google.com/app/apikey"
                      target="_blank"
                      rel="noreferrer"
                      className="underline font-semibold text-blue-700 hover:text-blue-900"
                    >
                      Google AI Studio
                    </a>
                  </li>
                  <li>Restart the backend development server to reload credentials.</li>
                </ol>
              </div>
            </div>
            <button
              onClick={() => setShowConfigHelp(false)}
              className="text-amber-700 hover:text-amber-950 font-bold ml-2 text-sm"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {/* ── Message Thread ───────────────────────────────────────── */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm p-4 overflow-y-auto space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-[85%] ${
              msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white ${
                msg.role === 'user' ? 'bg-blue-600' : 'bg-slate-800'
              }`}
            >
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            {/* Bubble */}
            <div className="space-y-1.5 min-w-0">
              <div
                className={`p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed shadow-xs ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-xs'
                    : 'bg-slate-50 text-slate-800 border border-slate-200/80 rounded-tl-xs'
                }`}
              >
                {/* Message text with basic markdown formatting */}
                <div className="whitespace-pre-wrap space-y-2">
                  {msg.content}
                </div>
              </div>

              {/* Tool Execution Metadata Pills (Assistant only) */}
              {msg.tools_called && msg.tools_called.length > 0 && (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs">
                  <button
                    onClick={() => toggleTools(msg.id)}
                    className="flex items-center justify-between w-full font-semibold text-slate-700 hover:text-blue-600 transition-colors"
                  >
                    <span className="flex items-center gap-1.5 text-[11px]">
                      <Wrench className="w-3 h-3 text-blue-500" />
                      Executed {msg.tools_called.length} backend {msg.tools_called.length === 1 ? 'tool' : 'tools'}
                    </span>
                    {expandedTools[msg.id] ? (
                      <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </button>

                  {expandedTools[msg.id] && (
                    <div className="mt-2 pt-2 border-t border-slate-200 space-y-1.5 text-[11px]">
                      {msg.tools_called.map((tool, idx) => (
                        <div key={idx} className="bg-white p-2 rounded border border-slate-200">
                          <p className="font-mono font-bold text-blue-600">{tool.tool_name}</p>
                          {tool.arguments && Object.keys(tool.arguments).length > 0 && (
                            <p className="text-slate-500 text-[10px] font-mono mt-0.5">
                              Args: {JSON.stringify(tool.arguments)}
                            </p>
                          )}
                          <p className="text-slate-600 text-[10px] font-mono mt-0.5 truncate">
                            Result: {JSON.stringify(tool.result_summary)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <p
                className={`text-[10px] text-slate-400 px-1 ${
                  msg.role === 'user' ? 'text-right' : 'text-left'
                }`}
              >
                {msg.timestamp}
              </p>
            </div>
          </div>
        ))}

        {/* Loading typing indicator */}
        {loading && (
          <div className="flex gap-3 max-w-[80%] mr-auto">
            <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-slate-800 text-white">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-slate-50 border border-slate-200 p-3 rounded-2xl rounded-tl-xs flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
              <span className="text-xs text-slate-500 font-medium">
                Gemini is consulting kitchen database tools…
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Suggested Questions Carousel / Wrap ───────────────────── */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-1 px-1 scrollbar-none shrink-0">
        <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1 shrink-0 mr-1">
          <Sparkles className="w-3 h-3 text-blue-500" />
          Try asking:
        </span>
        {SUGGESTED_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            disabled={loading}
            onClick={() => handleSend(prompt)}
            className="text-[11px] font-medium bg-white hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-200 px-2.5 py-1 rounded-full whitespace-nowrap transition-colors shadow-2xs disabled:opacity-50"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* ── Input Box ────────────────────────────────────────────── */}
      <div className="bg-white rounded-xl border border-slate-200 p-2 shadow-sm flex items-center gap-2 shrink-0">
        <input
          ref={inputRef}
          type="text"
          value={input}
          disabled={loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            status?.is_configured
              ? 'Ask anything about inventory, sales, consumption, or procurement…'
              : 'Ask a question (API key required for live Gemini reasoning)…'
          }
          className="flex-1 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none disabled:bg-slate-50"
        />

        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="flex items-center justify-center p-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white rounded-lg transition-colors shadow-xs"
          title="Send message"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin text-white" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>

    </div>
  );
}
