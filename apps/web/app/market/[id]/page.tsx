'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  Star, Users, MessageSquare, ArrowLeft, Sparkles,
  MessageCircle, Edit2, Trash2, X, Check, Send
} from 'lucide-react';
import { motion } from 'framer-motion';
import { marketApi } from '@/lib/api';
import { IdentityCardButton } from '@/components/IdentityCard';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/auth';

interface AvatarDetail {
  id: string;
  name: string;
  description?: string;
  avatar_type: string;
  creator_name: string;
  category: string;
  tags: string[];
  rating: number;
  usage_count: number;
  review_count: number;
  features: Array<{ name: string; description: string }>;
  is_featured: boolean;
  created_at: string;
}

interface Review {
  id: string;
  user_id: string;
  username?: string;
  rating: number;
  comment?: string;
  created_at: string;
  updated_at?: string;
  is_owner: boolean;
}

export default function AvatarDetailPage() {
  const params = useParams();
  const router = useRouter();
  const avatarId = params.id as string;
  const { isAuthenticated, user } = useAuthStore();
  
  const [avatar, setAvatar] = useState<AvatarDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  
  // 评价相关状态
  const [reviews, setReviews] = useState<Review[]>([]);
  const [myReview, setMyReview] = useState<Review | null>(null);
  const [isLoadingReviews, setIsLoadingReviews] = useState(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [editingReview, setEditingReview] = useState(false);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [showReviewForm, setShowReviewForm] = useState(false);


  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await marketApi.getAvatarDetail(avatarId);
        setAvatar(res as AvatarDetail);
      } catch (error) {
        console.error('Failed to load avatar:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [avatarId]);
  
  // 加载评价列表
  const loadReviews = async () => {
    setIsLoadingReviews(true);
    try {
      const res = await marketApi.getReviews(avatarId, { page: 1, page_size: 20 });
      console.log('Reviews loaded:', res);
      // 确保 res 是数组
      const reviewsArray = Array.isArray(res) ? res : (res as any)?.items || [];
      setReviews(reviewsArray as Review[]);
    } catch (error) {
      console.error('Failed to load reviews:', error);
    } finally {
      setIsLoadingReviews(false);
    }
  };
  
  // 加载当前用户的评价
  const loadMyReview = async () => {
    // 未登录用户不需要获取自己的评价
    if (!isAuthenticated) {
      setMyReview(null);
      return;
    }
    try {
      const res = await marketApi.getMyReview(avatarId);
      console.log('My review loaded:', res);
      if (res) {
        const review = res as unknown as Review;
        setMyReview(review);
        setRating(review.rating);
        setComment(review.comment || '');
      }
    } catch (error: any) {
      // 401 表示未登录，静默处理
      if (error?.response?.status === 401) {
        console.log('User not authenticated, skipping my-review');
        setMyReview(null);
        return;
      }
      // 404 表示没有评价过，忽略错误
      if (error?.response?.status === 404) {
        console.log('No review found for current user');
        setMyReview(null);
        return;
      }
      console.error('Error loading my review:', error);
    }
  };
  
  useEffect(() => {
    loadReviews();
    // 只有当明确登录后才加载当前用户的评价
    if (isAuthenticated === true) {
      loadMyReview();
    } else {
      // 未登录时重置评价状态
      setMyReview(null);
    }
  }, [avatarId, isAuthenticated]);

  const handleStartChat = async () => {
    // 检查是否已登录
    if (!isAuthenticated) {
      setShowLoginPrompt(true);
      return;
    }
    
    try {
      // 直接跳转到聊天页面并传递avatar参数，让聊天页面创建对话
      router.push(`/chat?avatar=${avatarId}`);
    } catch (error) {
      console.error('Failed to start chat:', error);
    }
  };
  
  const handleLogin = () => {
    const currentUrl = window.location.href;
    router.push(`/auth/login?redirect=${encodeURIComponent(currentUrl)}`);
  };
  
  // 提交评价
  const handleSubmitReview = async () => {
    if (!isAuthenticated) {
      setShowLoginPrompt(true);
      return;
    }
    
    if (rating < 1 || rating > 5) {
      alert('请选择评分');
      return;
    }
    
    setIsSubmittingReview(true);
    try {
      if (myReview) {
        // 更新评价
        await marketApi.updateReview(avatarId, { rating, comment });
      } else {
        // 创建评价
        await marketApi.createReview(avatarId, { rating, comment });
      }
      // 重新加载评价
      await loadReviews();
      await loadMyReview();
      setShowReviewForm(false);
      setEditingReview(false);
    } catch (error) {
      console.error('Failed to submit review:', error);
      alert('提交评价失败，请重试');
    } finally {
      setIsSubmittingReview(false);
    }
  };
  
  // 删除评价
  const handleDeleteReview = async () => {
    if (!confirm('确定要删除这条评价吗？')) return;
    
    try {
      await marketApi.deleteReview(avatarId);
      setMyReview(null);
      setRating(5);
      setComment('');
      await loadReviews();
    } catch (error) {
      console.error('Failed to delete review:', error);
      alert('删除评价失败');
    }
  };
  
  // 开始编辑评价
  const handleEditReview = () => {
    if (myReview) {
      setRating(myReview.rating);
      setComment(myReview.comment || '');
      setEditingReview(true);
      setShowReviewForm(true);
    }
  };
  
  // 取消编辑
  const handleCancelEdit = () => {
    setShowReviewForm(false);
    setEditingReview(false);
    if (myReview) {
      setRating(myReview.rating);
      setComment(myReview.comment || '');
    } else {
      setRating(5);
      setComment('');
    }
  };

  if (isLoading || !avatar) {
    return <div className="p-8 text-center">加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900"
          >
            <ArrowLeft className="w-5 h-5" />
            返回市场
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
              <div className="h-48 bg-gradient-to-br from-indigo-500 to-purple-600 relative">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-32 h-32 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white text-6xl font-bold">
                    {avatar.name.charAt(0)}
                  </div>
                </div>
              </div>
              
              <div className="p-8">
                <h1 className="text-3xl font-bold text-slate-900 mb-4">{avatar.name}</h1>
                <p className="text-slate-600 mb-6">{avatar.description || '暂无描述'}</p>
                
                <div className="flex items-center gap-6 text-sm text-slate-500 mb-6">
                  <span className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-amber-400" />
                    {avatar.rating.toFixed(1)} ({avatar.review_count} 评价)
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageSquare className="w-4 h-4" />
                    {avatar.usage_count} 次使用
                  </span>
                  <span className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    {avatar.creator_name}
                  </span>
                </div>

                {avatar.features.length > 0 && (
                  <div className="mb-6">
                    <h3 className="font-semibold text-slate-900 mb-3">认知特征</h3>
                    <div className="space-y-2">
                      {avatar.features.map((feature, idx) => (
                        <div key={idx} className="flex items-start gap-2">
                          <Sparkles className="w-4 h-4 text-indigo-500 mt-1" />
                          <div>
                            <span className="font-medium text-slate-700">{feature.name}</span>
                            <p className="text-sm text-slate-500">{feature.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {avatar.tags.length > 0 && (
                  <div className="flex gap-2 flex-wrap">
                    {avatar.tags.map((tag) => (
                      <span key={tag} className="px-3 py-1 bg-slate-100 text-slate-600 text-sm rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* 评价区域 */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">用户评价</h3>
                  <p className="text-sm text-slate-500 mt-1">
                    {avatar.review_count} 条评价 · 平均 {avatar.rating.toFixed(1)} 分
                  </p>
                </div>
                {!showReviewForm && (
                  <button
                    onClick={() => {
                      if (!isAuthenticated) {
                        setShowLoginPrompt(true);
                        return;
                      }
                      setShowReviewForm(true);
                    }}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 flex items-center gap-2"
                  >
                    <Star className="w-4 h-4" />
                    {myReview ? '修改评价' : '写评价'}
                  </button>
                )}
              </div>
              
              {/* 评价表单 */}
              {showReviewForm && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mb-6 p-4 bg-slate-50 rounded-xl"
                >
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      评分
                    </label>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          onClick={() => setRating(star)}
                          className="p-1 transition-colors"
                        >
                          <Star
                            className={cn(
                              'w-8 h-8',
                              star <= rating ? 'fill-amber-400 text-amber-400' : 'text-slate-300'
                            )}
                          />
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      评价内容（可选）
                    </label>
                    <textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="分享你的使用体验..."
                      rows={4}
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-none"
                    />
                  </div>
                  
                  <div className="flex gap-3">
                    <button
                      onClick={handleSubmitReview}
                      disabled={isSubmittingReview}
                      className="flex-1 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {isSubmittingReview ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          提交中...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          {editingReview ? '更新评价' : '提交评价'}
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 border border-slate-200 rounded-lg font-medium hover:bg-slate-100 transition-colors"
                    >
                      取消
                    </button>
                  </div>
                </motion.div>
              )}
              
              {/* 评价列表 */}
              <div className="space-y-4">
                {isLoadingReviews ? (
                  <div className="text-center py-8">
                    <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
                  </div>
                ) : reviews.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Star className="w-12 h-12 mx-auto mb-3 text-slate-200" />
                    <p>还没有评价</p>
                    <p className="text-sm mt-1">成为第一个评价的人吧！</p>
                  </div>
                ) : (
                  reviews.map((review) => (
                    <div
                      key={review.id}
                      className={cn(
                        'p-4 rounded-xl border',
                        review.is_owner 
                          ? 'bg-indigo-50 border-indigo-100' 
                          : 'bg-slate-50 border-slate-100'
                      )}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
                            {(review.username || '匿名').charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-slate-900 text-sm">{review.username || '匿名用户'}</p>
                            <p className="text-xs text-slate-500">
                              {new Date(review.created_at).toLocaleDateString('zh-CN')}
                              {review.updated_at && ' (已修改)'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                          <span className="font-medium text-slate-900">{review.rating}</span>
                        </div>
                      </div>
                      
                      {review.comment && (
                        <p className="text-slate-600 text-sm mt-2">{review.comment}</p>
                      )}
                      
                      {review.is_owner && !showReviewForm && (
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={handleEditReview}
                            className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                          >
                            <Edit2 className="w-3 h-3" />
                            编辑
                          </button>
                          <button
                            onClick={handleDeleteReview}
                            className="text-xs text-red-500 hover:text-red-600 flex items-center gap-1"
                          >
                            <Trash2 className="w-3 h-3" />
                            删除
                          </button>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
              <h3 className="font-semibold text-slate-900 mb-4">使用分身</h3>
              <div className="space-y-3">
                <button
                  onClick={handleStartChat}
                  className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 flex items-center justify-center gap-2"
                >
                  <MessageCircle className="w-5 h-5" />
                  开始对话
                </button>
                
                <IdentityCardButton 
                  avatarId={avatarId} 
                  color="from-purple-500 to-pink-600"
                  size="lg"
                />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
              <h3 className="font-semibold text-slate-900 mb-4">统计信息</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">分类</span>
                  <span className="font-medium">{avatar.category}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">类型</span>
                  <span className="font-medium">{avatar.avatar_type === 'celebrity' ? '名人' : '用户创建'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">创建时间</span>
                  <span className="font-medium">{new Date(avatar.created_at).toLocaleDateString('zh-CN')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 登录提示弹窗 */}
      {showLoginPrompt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl max-w-md w-full p-6"
          >
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">需要登录</h3>
              <p className="text-slate-600 mb-6">
                与分身对话需要先登录账号<br/>
                登录后即可开始与 {avatar?.name} 交流
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowLoginPrompt(false)}
                  className="flex-1 px-4 py-3 border border-slate-200 rounded-lg font-medium hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleLogin}
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                >
                  去登录
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
