'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Sparkles, Plus, Search, MessageSquare, Trash2, Loader2 } from 'lucide-react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { cn } from '@/lib/utils';
import { apiRequest, useAuthStore } from '@/lib/auth';
import { toast } from 'sonner';

interface Avatar {
  id: string;
  name: string;
  description?: string;
  avatar_type: string;
  status: string;
  is_public: boolean;
}

interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_name?: string;
  content: string;
  is_user?: boolean;  // 是否是用户发送的消息
  emotion_state?: { pleasure: number; arousal: number; dominance: number };
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  avatar_id?: string;
  participants?: Array<{ id: string; name: string; avatar_type: string; description?: string }>;
  last_message?: { content: string; created_at: string } | null;
  updated_at: string;
}

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialAvatarId = searchParams.get('avatar');
  const { isAuthenticated } = useAuthStore();
  
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [selectedAvatarId, setSelectedAvatarId] = useState<string | null>(initialAvatarId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showNewChat, setShowNewChat] = useState(false);
  const [hoveredConversation, setHoveredConversation] = useState<string | null>(null);
  const [deletingConversation, setDeletingConversation] = useState<string | null>(null);
  const [isClearingAll, setIsClearingAll] = useState(false);
  const hasCreatedConversation = useRef(false);

  // 加载分身列表
  const loadAvatars = useCallback(async () => {
    try {
      const data = await apiRequest('/avatars/my/avatars');
      setAvatars(data);
    } catch (error) {
      console.error('Failed to load avatars:', error);
    }
  }, []);

  // 加载对话列表
  const loadConversations = useCallback(async () => {
    try {
      const data = await apiRequest('/conversations');
      // API 返回的是数组或对象格式 { items: [...] }
      setConversations(Array.isArray(data) ? data : (data.items || []));
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, []);

  // 加载消息
  const loadMessages = useCallback(async (conversationId: string) => {
    setIsLoading(true);
    try {
      const data = await apiRequest(`/conversations/${conversationId}/messages`);
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadAvatars();
      loadConversations();
    }
  }, [isAuthenticated, loadAvatars, loadConversations]);

  // 处理初始 avatarId - 如果URL中有avatar参数，检查登录状态后创建对话
  useEffect(() => {
    if (initialAvatarId && !hasCreatedConversation.current) {
      hasCreatedConversation.current = true;
      // 检查是否已登录
      if (!isAuthenticated) {
        // 未登录，跳转到登录页面，并携带当前URL作为redirect参数
        const currentUrl = typeof window !== 'undefined' ? window.location.href : `/chat?avatar=${initialAvatarId}`;
        router.push(`/auth/login?redirect=${encodeURIComponent(currentUrl)}`);
        return;
      }
      startNewConversation(initialAvatarId);
    }
  }, [initialAvatarId, isAuthenticated, router]);

  const startNewConversation = async (avatarId: string) => {
    // 检查是否已登录
    if (!isAuthenticated) {
      const currentUrl = typeof window !== 'undefined' ? window.location.href : `/chat?avatar=${avatarId}`;
      router.push(`/auth/login?redirect=${encodeURIComponent(currentUrl)}`);
      return;
    }
    
    try {
      const data = await apiRequest('/conversations', {
        method: 'POST',
        body: JSON.stringify({
          participant_ids: [avatarId],
          title: '新对话',
        }),
      });
      setSelectedConversation(data.id);
      setSelectedAvatarId(avatarId);
      setShowNewChat(false);
      await loadConversations();
      // 加载新对话的消息（可能为空）
      await loadMessages(data.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
      alert('创建对话失败');
    }
  };

  const handleSelectConversation = async (conversationId: string, avatarId: string) => {
    setSelectedConversation(conversationId);
    setSelectedAvatarId(avatarId);
    setShowNewChat(false);
    await loadMessages(conversationId);
  };

  const handleDeleteConversation = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止触发选中对话
    
    if (!confirm('确定要删除这个对话吗？所有消息将被永久删除，此操作不可恢复。')) {
      return;
    }
    
    setDeletingConversation(conversationId);
    try {
      await apiRequest(`/conversations/${conversationId}`, {
        method: 'DELETE',
      });
      
      // 如果删除的是当前选中的对话，清空选中状态
      if (selectedConversation === conversationId) {
        setSelectedConversation(null);
        setSelectedAvatarId(null);
        setMessages([]);
        setShowNewChat(true);
      }
      
      // 刷新对话列表
      await loadConversations();
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('删除对话失败，请重试');
    } finally {
      setDeletingConversation(null);
    }
  };

  // 一键清空所有对话
  const handleClearAllConversations = async () => {
    if (conversations.length === 0) {
      toast.info('暂无对话需要清空');
      return;
    }
    
    if (!confirm(`确定要清空所有 ${conversations.length} 个对话吗？所有消息将被永久删除，此操作不可恢复。`)) {
      return;
    }
    
    setIsClearingAll(true);
    try {
      // 串行删除所有对话
      for (const conversation of conversations) {
        await apiRequest(`/conversations/${conversation.id}`, {
          method: 'DELETE',
        });
      }
      
      // 清空当前选中状态
      setSelectedConversation(null);
      setSelectedAvatarId(null);
      setMessages([]);
      setShowNewChat(true);
      
      // 刷新对话列表
      await loadConversations();
      toast.success(`已清空所有 ${conversations.length} 个对话`);
    } catch (error) {
      console.error('Failed to clear all conversations:', error);
      toast.error('清空对话失败，请重试');
    } finally {
      setIsClearingAll(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedConversation) return;
    
    setIsSending(true);
    
    // 乐观更新：先添加用户消息到列表
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: selectedConversation,
      sender_id: selectedAvatarId || 'user',
      content,
      is_user: true,  // 标记为用户消息
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMessage]);
    
    try {
      // 发送消息到 API
      const data = await apiRequest(`/conversations/${selectedConversation}/messages`, {
        method: 'POST',
        body: JSON.stringify({ content }),
      });
      
      // 重新加载消息列表以获取用户消息和 AI 回复
      await loadMessages(selectedConversation);
      
      // 刷新对话列表以更新最后消息
      await loadConversations();
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('发送失败，请重试');
      // 移除临时消息
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id));
    } finally {
      setIsSending(false);
    }
  };

  // 从当前选中的对话中获取分身信息（优先从 participants，支持系统分身）
  const currentConversation = conversations.find(c => c.id === selectedConversation);
  const currentAvatarFromAPI = currentConversation?.participants?.[0];
  const currentAvatarFromLocal = avatars.find(a => a.id === selectedAvatarId);
  const currentAvatar = currentAvatarFromAPI || currentAvatarFromLocal;
  
  // 过滤对话列表
  const filteredConversations = conversations.filter(conv => {
    // 优先从后端返回的 participants 获取分身名称（支持系统分身）
    const avatarName = conv.participants?.[0]?.name || 
      avatars.find(a => a.id === (conv.avatar_id || conv.participants?.[0]?.id))?.name ||
      '';
    return avatarName.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // 可用的分身（状态为 ready）
  const availableAvatars = avatars.filter(a => a.status === 'ready');

  return (
    <div className="h-screen flex bg-slate-50">
      {/* 侧边栏 */}
      <div className="w-80 bg-white border-r flex flex-col">
        {/* 头部 */}
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg">对话</span>
          </div>
          
          <button 
            onClick={() => {
              setShowNewChat(true);
              setSelectedConversation(null);
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            新建对话
          </button>
        </div>

        {/* 搜索 */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="搜索对话..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
        </div>

        {/* 对话统计与操作 */}
        {conversations.length > 0 && (
          <div className="px-4 py-2 border-b bg-slate-50/50 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              共 {conversations.length} 个对话
            </span>
            <button
              onClick={handleClearAllConversations}
              disabled={isClearingAll}
              className="flex items-center gap-1 text-xs text-red-500 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isClearingAll ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Trash2 className="w-3 h-3" />
              )}
              清空所有
            </button>
          </div>
        )}

        {/* 对话列表 */}
        <div className="flex-1 overflow-y-auto p-2">
          {filteredConversations.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="w-12 h-12 text-slate-200 mx-auto mb-3" />
              <p className="text-sm text-slate-500">暂无对话</p>
              <p className="text-xs text-slate-400 mt-1">点击上方按钮开始新对话</p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredConversations.map((conversation) => {
                // 优先从后端返回的 participants 获取分身信息（支持系统分身）
                // 如果 participants 不存在，再从本地 avatars 查找
                const participantFromAPI = conversation.participants?.[0];
                const participantId = conversation.avatar_id || participantFromAPI?.id;
                const avatarFromLocal = avatars.find(a => a.id === participantId);
                // 优先使用后端返回的分身信息，其次是本地缓存
                const avatar = participantFromAPI || avatarFromLocal;
                const lastMessageContent = typeof conversation.last_message === 'string' 
                  ? conversation.last_message 
                  : conversation.last_message?.content;
                const isHovered = hoveredConversation === conversation.id;
                const isDeleting = deletingConversation === conversation.id;
                return (
                  <button
                    key={conversation.id}
                    onClick={() => handleSelectConversation(conversation.id, participantId || '')}
                    onMouseEnter={() => setHoveredConversation(conversation.id)}
                    onMouseLeave={() => setHoveredConversation(null)}
                    disabled={isDeleting}
                    className={cn(
                      'w-full flex items-center gap-3 p-3 rounded-lg transition-all text-left group relative',
                      selectedConversation === conversation.id && !showNewChat
                        ? 'bg-indigo-50 border border-indigo-100'
                        : 'hover:bg-slate-50',
                      isDeleting && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-medium flex-shrink-0">
                      {avatar?.name?.charAt(0) || '?'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 truncate">{avatar?.name || '未知分身'}</p>
                      <p className="text-xs text-slate-500 truncate">
                        {lastMessageContent || '点击开始对话'}
                      </p>
                    </div>
                    {/* 删除按钮 - 悬停时显示 */}
                    {isHovered && !isDeleting && (
                      <button
                        onClick={(e) => handleDeleteConversation(conversation.id, e)}
                        className="p-1.5 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors flex-shrink-0"
                        title="删除对话"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                    {isDeleting && (
                      <div className="w-4 h-4 border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin flex-shrink-0" />
                    )}
                  </button>
                );
              })} 
            </div>
          )}
        </div>
      </div>

      {/* 主聊天区 */}
      <div className="flex-1">
        {showNewChat ? (
          // 新建对话 - 选择分身
          <div className="h-full flex items-center justify-center bg-slate-50">
            <div className="max-w-2xl w-full mx-auto p-8">
              <div className="text-center mb-8">
                <div className="w-16 h-16 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-8 h-8 text-indigo-500" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">选择一个分身开始对话</h3>
                <p className="text-slate-500">每个分身都有独特的思维方式和认知特征</p>
              </div>
              
              {availableAvatars.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-slate-500 mb-4">还没有可用的分身</p>
                  <a 
                    href="/avatar/create" 
                    className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                  >
                    创建分身
                  </a>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  {availableAvatars.map((avatar) => (
                    <button
                      key={avatar.id}
                      onClick={() => startNewConversation(avatar.id)}
                      className="flex items-center gap-4 p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all text-left"
                    >
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-lg font-medium">
                        {avatar.name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-slate-900 truncate">{avatar.name}</p>
                        <p className="text-sm text-slate-500 truncate">{avatar.description || '基于真实认知特征构建'}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : selectedConversation ? (
          <ChatInterface
            conversationId={selectedConversation}
            avatar={currentAvatar}
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading || isSending}
          />
        ) : (
          // 空状态
          <div className="h-full flex items-center justify-center bg-slate-50">
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-10 h-10 text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">开始与数字分身对话</h3>
              <p className="text-slate-500 mb-8 max-w-md">与基于真实认知特征构建的数字分身进行深度对话，探索不同思维方式的碰撞</p>
              <button
                onClick={() => setShowNewChat(true)}
                className="px-8 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors"
              >
                选择分身开始对话
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
