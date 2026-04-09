'use client';

import Link from 'next/link';
import { Shield, Lock, Eye, Trash2, Database } from 'lucide-react';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-900">Human.online</span>
          </Link>
          <Link href="/" className="text-sm text-slate-500 hover:text-slate-900">
            返回首页
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-white rounded-2xl shadow-sm border p-8 md:p-12">
          <h1 className="text-3xl font-bold text-slate-900 mb-4">隐私政策</h1>
          <p className="text-slate-500 mb-8">最后更新日期：2024年1月</p>

          <div className="prose prose-slate max-w-none">
            <p className="text-slate-600 leading-relaxed mb-6">
              Human.online 高度重视您的隐私保护。本隐私政策说明我们如何收集、使用、存储和保护您的个人信息。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              信息收集
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              我们可能收集以下类型的信息：
            </p>
            <ul className="list-disc list-inside text-slate-600 space-y-2 mb-6">
              <li><strong>账户信息：</strong>当您注册时，我们会收集您的邮箱地址、用户名等基本信息。</li>
              <li><strong>对话数据：</strong>您上传的聊天记录、书籍文章等用于构建数字分身的材料。</li>
              <li><strong>使用数据：</strong>您与分身的对话记录、使用频率等功能使用数据。</li>
              <li><strong>技术信息：</strong>IP地址、浏览器类型、设备信息等用于优化服务的技术数据。</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4 flex items-center gap-2">
              <Lock className="w-5 h-5 text-indigo-600" />
              数据安全
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              我们采用行业标准的加密和安全措施保护您的数据：
            </p>
            <ul className="list-disc list-inside text-slate-600 space-y-2 mb-6">
              <li>所有数据传输使用 TLS/SSL 加密</li>
              <li>敏感数据在数据库中加密存储</li>
              <li>定期安全审计和漏洞扫描</li>
              <li>严格的内部数据访问控制</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4 flex items-center gap-2">
              <Eye className="w-5 h-5 text-indigo-600" />
              数据使用
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              我们使用您的数据用于以下目的：
            </p>
            <ul className="list-disc list-inside text-slate-600 space-y-2 mb-6">
              <li>构建和维护您的数字分身</li>
              <li>提供和改进我们的服务</li>
              <li>个性化用户体验</li>
              <li>发送服务相关的通知</li>
              <li>防止欺诈和滥用</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4 flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-indigo-600" />
              数据删除
            </h2>
            <p className="text-slate-600 leading-relaxed mb-6">
              您随时可以删除您的账户和相关数据。删除账户后，我们将在30天内永久删除您的所有个人数据，
              包括数字分身、对话记录和上传的文件。请注意，此操作不可逆转。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              第三方服务
            </h2>
            <p className="text-slate-600 leading-relaxed mb-6">
              我们可能使用第三方服务提供商来处理数据，包括云存储服务（如 AWS、阿里云）、
              AI 服务提供商（如 OpenAI、Kimi）等。这些提供商受合同约束，仅可按我们的指示处理数据，
              并有义务保护您的隐私。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              联系我们
            </h2>
            <p className="text-slate-600 leading-relaxed">
              如果您对本隐私政策有任何疑问，请通过以下方式联系我们：
            </p>
            <p className="text-slate-600 mt-2">
              邮箱：privacy@human.online
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 px-6 border-t bg-white">
        <div className="max-w-4xl mx-auto text-center text-sm text-slate-500">
          <p>© 2024 Human.online. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
