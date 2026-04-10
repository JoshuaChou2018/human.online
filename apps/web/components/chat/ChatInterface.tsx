'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

interface ChatAvatar {
  id: string;
  name: string;
  description?: string;
}

interface ChatMessage {
  id: string;
  sender_id: string;
  sender_name?: string;
  content: string;
  is_user?: boolean;  // 是否是用户发送的消息
  emotion_state?: { pleasure: number; arousal: number; dominance: number };
  created_at: string;
}

interface ChatInterfaceProps {
  conversationId?: string;
  avatar?: ChatAvatar;
  onSendMessage: (content: string) => void;
  messages: ChatMessage[];
  isLoading?: boolean;
}

export function ChatInterface({
  avatar,
  onSendMessage,
  messages,
  isLoading,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/50">
      {/* 头部 */}
      <div className="flex items-center justify-between px-6 py-4 border-b bg-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-medium">
            {avatar?.name?.charAt(0) || '?'}
          </div>
          <div>
            <h3 className="font-medium text-slate-900">
              {avatar?.name || '未知分身'}
            </h3>
            <p className="text-xs text-slate-500">
              {avatar?.description || '基于真实认知特征构建'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span className="text-xs text-slate-500">AI 驱动对话</span>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <div className="w-16 h-16 rounded-full bg-indigo-50 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-indigo-400" />
            </div>
            <p className="text-sm">开始与 {avatar?.name || '分身'} 对话</p>
            <p className="text-xs mt-1 text-slate-400">每个分身都基于真实认知特征构建</p>
          </div>
        )}

        {messages.map((message, index) => {
          const isCurrentUser = message.is_user;
          const showAvatar = index === 0 || messages[index - 1].sender_id !== message.sender_id;

          return (
            <div
              key={message.id}
              className={cn(
                'flex gap-3',
                isCurrentUser ? 'flex-row-reverse' : 'flex-row'
              )}
            >
              {showAvatar ? (
                <div className="w-8 h-8 rounded-full flex-shrink-0 overflow-hidden">
                  {isCurrentUser ? (
                    <div className="w-full h-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xs font-medium">
                      <User className="w-4 h-4" />
                    </div>
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-medium">
                      {avatar?.name?.charAt(0) || '?'}
                    </div>
                  )}
                </div>
              ) : (
                <div className="w-8 flex-shrink-0" />
              )}

              <div
                className={cn(
                  'max-w-[70%]',
                  isCurrentUser ? 'items-end' : 'items-start'
                )}
              >
                {showAvatar && (
                  <p className="text-xs text-slate-500 mb-1 px-1">
                    {isCurrentUser ? '我' : avatar?.name}
                  </p>
                )}
                <div
                  className={cn(
                    'px-4 py-2.5 rounded-2xl text-sm leading-relaxed prose prose-sm max-w-none',
                    '[&_p]:mb-2 [&_p:last-child]:mb-0',
                    '[&_ul]:mb-2 [&_ul]:ml-4 [&_ol]:mb-2 [&_ol]:ml-4',
                    '[&_li]:mb-0.5',
                    '[&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-xs [&_code]:font-mono',
                    isCurrentUser
                      ? 'bg-blue-600 text-white rounded-br-md prose-invert [&_code]:bg-blue-500/50 [&_pre]:bg-blue-500/30 [&_pre]:p-2 [&_pre]:rounded-lg [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_a]:text-blue-100 [&_a]:underline'
                      : 'bg-white border border-slate-200 text-slate-700 rounded-bl-md shadow-sm [&_code]:bg-slate-100 [&_code]:text-slate-800 [&_pre]:bg-slate-800 [&_pre]:p-2 [&_pre]:rounded-lg [&_pre_code]:bg-transparent [&_pre_code]:text-slate-100 [&_pre_code]:p-0 [&_a]:text-blue-600 [&_a]:underline'
                  )}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
                {message.emotion_state && !isCurrentUser && (
                  <div className="flex items-center gap-1 mt-1 px-1">
                    <div
                      className={cn(
                        'w-2 h-2 rounded-full',
                        message.emotion_state.pleasure > 0
                          ? 'bg-green-400'
                          : message.emotion_state.pleasure < 0
                          ? 'bg-red-400'
                          : 'bg-slate-300'
                      )}
                    />
                    <span className="text-[10px] text-slate-400">
                      {message.emotion_state.pleasure > 0.3
                        ? '积极'
                        : message.emotion_state.pleasure < -0.3
                        ? '消极'
                        : '中性'}
                    </span>
                  </div>
                )}
                <span className="text-[10px] text-slate-400 mt-1 block">
                  {formatTime(message.created_at)}
                </span>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-medium flex-shrink-0">
              {avatar?.name?.charAt(0) || '?'}
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" />
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-100" />
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-200" />
                </div>
                <span className="text-xs text-slate-500">
                  {avatar?.name || '分身'} 正在思考...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="px-6 py-4 bg-white border-t">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`给 ${avatar?.name || '分身'} 发送消息...`}
              className="w-full px-4 py-3 pr-12 bg-slate-50 border border-slate-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              rows={1}
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={cn(
              'p-3 rounded-xl transition-all',
              input.trim() && !isLoading
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/25'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-[10px] text-slate-400 mt-2 text-center">
          数字分身基于 MindWeave 技术构建，回复内容反映其独特思维方式
        </p>
      </div>
    </div>
  );
}
