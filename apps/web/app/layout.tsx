import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from 'sonner';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Human.online - 构建你的数字分身',
  description: '上传聊天记录、书籍文章，AI 将提取你的认知特征，构建一个拥有你思维方式的数字分身。在数字社会中与名人分身对话，测试言论的社会影响。',
  keywords: '数字分身, AI, 认知蒸馏, 社会模拟, chatbot, digital twin',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        {children}
        <Toaster position="top-center" richColors />
      </body>
    </html>
  );
}
