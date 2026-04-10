'use client';

import { useRouter } from 'next/navigation';
import { Home } from 'lucide-react';

interface BackToHomeProps {
  className?: string;
}

export function BackToHome({ className = '' }: BackToHomeProps) {
  const router = useRouter();

  return (
    <button
      onClick={() => router.push('/')}
      className={`fixed top-4 left-4 z-50 flex items-center gap-2 px-3 py-2 bg-white/90 backdrop-blur-md text-slate-700 rounded-lg shadow-lg border border-slate-200 hover:bg-white hover:shadow-xl transition-all ${className}`}
      title="回到主页"
    >
      <Home className="w-4 h-4" />
      <span className="text-sm font-medium hidden sm:inline">主页</span>
    </button>
  );
}
