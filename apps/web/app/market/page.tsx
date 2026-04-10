'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { BackToHome } from '@/components/BackToHome';
import { 
  Search, 
  Filter, 
  Star, 
  Users, 
  MessageSquare, 
  TrendingUp, 
  Clock,
  ChevronRight,
  Sparkles,
  Copy,
  CheckCircle2,
  Zap,
  User
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { marketApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import { AvatarType } from '@/types';

interface Category {
  id: string;
  name: string;
  icon: string;
  description: string;
}

interface MarketAvatar {
  id: string;
  name: string;
  description?: string;
  avatar_type: AvatarType;
  creator_name: string;
  creator_avatar?: string;
  category: string;
  tags: string[];
  rating: number;
  usage_count: number;
  review_count: number;
  features: Array<{ name: string; description: string }>;
  is_featured: boolean;
  created_at: string;
}

const sortOptions = [
  { value: 'popular', label: '最受欢迎', icon: TrendingUp },
  { value: 'newest', label: '最新发布', icon: Clock },
  { value: 'rating', label: '评分最高', icon: Star },
  { value: 'usage', label: '使用最多', icon: Users },
];

export default function MarketPage() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [avatars, setAvatars] = useState<MarketAvatar[]>([]);
  const [featuredAvatars, setFeaturedAvatars] = useState<MarketAvatar[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('popular');
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [showFilters, setShowFilters] = useState(false);

  // 加载分类和精选分身
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [categoriesRes, featuredRes] = await Promise.all([
          marketApi.getCategories(),
          marketApi.getFeatured(6),
        ]);
        setCategories(categoriesRes as Category[]);
        setFeaturedAvatars(featuredRes as MarketAvatar[]);
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };
    loadInitialData();
  }, []);

  // 加载分身列表
  useEffect(() => {
    const loadAvatars = async () => {
      setIsLoading(true);
      try {
        const res = await marketApi.getAvatars({
          category: selectedCategory || undefined,
          search: searchQuery || undefined,
          sort_by: sortBy,
          page,
          page_size: 20,
        });
        setAvatars((res as { items: MarketAvatar[] }).items);
        setTotal((res as { total: number }).total);
      } catch (error) {
        console.error('Failed to load avatars:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadAvatars();
  }, [selectedCategory, searchQuery, sortBy, page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory(selectedCategory === categoryId ? '' : categoryId);
    setPage(1);
  };

  const handleAvatarClick = (avatarId: string) => {
    router.push(`/market/${avatarId}`);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <BackToHome />
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="text-center max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur rounded-full text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                探索社区创建的数字分身
              </div>
              <h1 className="text-4xl md:text-6xl font-bold mb-6">
                分身市场
              </h1>
              <p className="text-xl text-white/80 mb-8">
                发现和使用由社区创建的数字分身。与名人对话，探索不同的思维方式。
              </p>
            </motion.div>

            {/* Search Bar */}
            <motion.form
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              onSubmit={handleSearch}
              className="relative max-w-2xl mx-auto"
            >
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="搜索分身、标签或创建者..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 rounded-2xl bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-white/30 shadow-2xl"
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors"
              >
                搜索
              </button>
            </motion.form>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Featured Section */}
        {featuredAvatars.length > 0 && !searchQuery && !selectedCategory && (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                <Zap className="w-6 h-6 text-amber-500" />
                精选分身
              </h2>
              <button 
                onClick={() => setSortBy('popular')}
                className="text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
              >
                查看全部
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredAvatars.map((avatar) => (
                <FeaturedAvatarCard
                  key={avatar.id}
                  avatar={avatar}
                  onClick={() => handleAvatarClick(avatar.id)}
                />
              ))}
            </div>
          </motion.section>
        )}

        {/* Categories */}
        <section className="mb-8">
          <div className="flex items-center gap-4 overflow-x-auto pb-4 scrollbar-hide">
            <button
              onClick={() => handleCategoryClick('')}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap transition-all',
                selectedCategory === ''
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              )}
            >
              全部
            </button>
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => handleCategoryClick(category.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap transition-all',
                  selectedCategory === category.id
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                )}
              >
                <span>{category.icon}</span>
                {category.name}
              </button>
            ))}
          </div>
        </section>

        {/* Filters and Sort */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg border transition-all',
                showFilters
                  ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              )}
            >
              <Filter className="w-4 h-4" />
              筛选
            </button>
            <span className="text-slate-500 text-sm">
              共 {total} 个分身
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-500 text-sm">排序:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Avatar Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <AvatarCardSkeleton key={i} />
            ))}
          </div>
        ) : avatars.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              <AnimatePresence mode="popLayout">
                {avatars.map((avatar, index) => (
                  <motion.div
                    key={avatar.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.2, delay: index * 0.05 }}
                  >
                    <AvatarCard
                      avatar={avatar}
                      onClick={() => handleAvatarClick(avatar.id)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {/* Pagination */}
            {total > 20 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
                >
                  上一页
                </button>
                <span className="px-4 py-2 text-slate-600">
                  第 {page} 页
                </span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={avatars.length < 20}
                  className="px-4 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// Featured Avatar Card
function FeaturedAvatarCard({ 
  avatar, 
  onClick 
}: { 
  avatar: MarketAvatar; 
  onClick: () => void;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      onClick={onClick}
      className="group relative bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all cursor-pointer overflow-hidden border border-slate-100"
    >
      <div className="absolute top-4 left-4 z-10">
        <span className="px-3 py-1 bg-amber-400 text-white text-xs font-bold rounded-full flex items-center gap-1">
          <Zap className="w-3 h-3" />
          精选
        </span>
      </div>
      
      <div className="h-48 bg-gradient-to-br from-indigo-500 to-purple-600 relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-24 h-24 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white text-4xl font-bold border-4 border-white/30">
            {avatar.name.charAt(0)}
          </div>
        </div>
      </div>
      
      <div className="p-6">
        <h3 className="text-xl font-bold text-slate-900 mb-2 group-hover:text-indigo-600 transition-colors">
          {avatar.name}
        </h3>
        <p className="text-slate-500 text-sm mb-4 line-clamp-2">
          {avatar.description || '暂无描述'}
        </p>
        
        <div className="flex items-center gap-4 text-sm text-slate-500 mb-4">
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 text-amber-400" />
            <span className="font-medium">{avatar.rating.toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageSquare className="w-4 h-4" />
            <span>{avatar.usage_count}</span>
          </div>
          <div className="flex items-center gap-1">
            <Copy className="w-4 h-4" />
            <span>{avatar.review_count}</span>
          </div>
        </div>
        
        {/* 创建者信息 */}
        <div className="flex items-center gap-2 pt-4 border-t border-slate-100">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-medium">
            {avatar.creator_name.charAt(0)}
          </div>
          <span className="text-sm text-slate-600">{avatar.creator_name}</span>
        </div>
      </div>
    </motion.div>
  );
}

// Regular Avatar Card
function AvatarCard({ 
  avatar, 
  onClick 
}: { 
  avatar: MarketAvatar; 
  onClick: () => void;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      onClick={onClick}
      className="group bg-white rounded-xl shadow-sm hover:shadow-lg transition-all cursor-pointer border border-slate-100 overflow-hidden"
    >
      <div className="h-32 bg-gradient-to-br from-slate-100 to-slate-200 relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-2xl font-bold">
            {avatar.name.charAt(0)}
          </div>
        </div>
        {avatar.avatar_type === 'celebrity' && (
          <div className="absolute top-2 right-2">
            <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
              名人
            </span>
          </div>
        )}
      </div>
      
      <div className="p-4">
        <h3 className="font-semibold text-slate-900 mb-1 group-hover:text-indigo-600 transition-colors truncate">
          {avatar.name}
        </h3>
        <p className="text-slate-500 text-xs mb-3 line-clamp-1">
          {avatar.description || '暂无描述'}
        </p>
        
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-1">
            <Star className="w-3 h-3 text-amber-400" />
            <span>{avatar.rating.toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            <span>{avatar.usage_count}</span>
          </div>
        </div>
        
        {/* 创建者信息 */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-100">
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-[10px] font-medium">
            {avatar.creator_name.charAt(0)}
          </div>
          <span className="text-xs text-slate-500 truncate">{avatar.creator_name}</span>
        </div>
        
        {avatar.tags.length > 0 && (
          <div className="flex gap-1 mt-3 flex-wrap">
            {avatar.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
            {avatar.tags.length > 2 && (
              <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-full">
                +{avatar.tags.length - 2}
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// Skeleton Loading
function AvatarCardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-slate-100 overflow-hidden animate-pulse">
      <div className="h-32 bg-slate-200" />
      <div className="p-4 space-y-3">
        <div className="h-5 bg-slate-200 rounded w-3/4" />
        <div className="h-3 bg-slate-200 rounded w-full" />
        <div className="flex gap-2">
          <div className="h-3 bg-slate-200 rounded w-16" />
          <div className="h-3 bg-slate-200 rounded w-16" />
        </div>
      </div>
    </div>
  );
}

// Empty State
function EmptyState() {
  return (
    <div className="text-center py-16">
      <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Search className="w-10 h-10 text-slate-400" />
      </div>
      <h3 className="text-lg font-semibold text-slate-900 mb-2">
        没有找到分身
      </h3>
      <p className="text-slate-500">
        尝试调整搜索条件或筛选选项
      </p>
    </div>
  );
}
