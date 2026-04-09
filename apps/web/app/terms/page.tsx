'use client';

import Link from 'next/link';
import { FileText, Scale, AlertCircle, CheckCircle } from 'lucide-react';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <FileText className="w-4 h-4 text-white" />
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
          <h1 className="text-3xl font-bold text-slate-900 mb-4">服务条款</h1>
          <p className="text-slate-500 mb-8">最后更新日期：2024年1月</p>

          <div className="prose prose-slate max-w-none">
            <p className="text-slate-600 leading-relaxed mb-6">
              欢迎使用 Human.online！请仔细阅读以下服务条款。使用我们的服务即表示您同意遵守这些条款。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-indigo-600" />
              服务概述
            </h2>
            <p className="text-slate-600 leading-relaxed mb-6">
              Human.online 是一个数字分身构建平台，允许用户上传个人数据（如聊天记录、文章等），
              使用 AI 技术分析和提取认知特征，创建个性化的数字分身。我们还提供社会模拟、
              分身对话等功能。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4 flex items-center gap-2">
              <Scale className="w-5 h-5 text-indigo-600" />
              用户责任
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              作为用户，您同意：
            </p>
            <ul className="list-disc list-inside text-slate-600 space-y-2 mb-6">
              <li>提供真实、准确的注册信息</li>
              <li>保护您的账户密码安全</li>
              <li>不上传侵犯他人版权或隐私的数据</li>
              <li>不上传违法、淫秽、暴力或仇恨内容</li>
              <li>不滥用服务进行垃圾信息传播或网络攻击</li>
              <li>对自己创建的分身和发布的内容负责</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              知识产权
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              <strong>您的内容：</strong>您保留上传内容的知识产权。通过上传内容，
              您授予我们必要的许可，用于提供、改进和维护服务。
            </p>
            <p className="text-slate-600 leading-relaxed mb-6">
              <strong>我们的服务：</strong>Human.online 平台、商标、代码、设计等知识产权归我们所有。
              未经授权，您不得复制、修改、分发或反编译我们的服务。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-indigo-600" />
              免责声明
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              数字分身是基于 AI 技术生成的模拟，具有以下限制：
            </p>
            <ul className="list-disc list-inside text-slate-600 space-y-2 mb-6">
              <li>数字分身不代表真实的您，其行为可能与您的真实想法不符</li>
              <li>AI 生成的内容可能存在错误或不准确</li>
              <li>我们不对因使用服务而产生的任何直接或间接损失负责</li>
              <li>服务可能因维护、升级或不可抗力而中断</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              付费服务
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              部分功能可能需要付费使用：
            </p>
            <ul className="list-disc list-inside text-slate-600 space-y-2 mb-6">
              <li>付费后，服务将在约定时间内生效</li>
              <li>除非法律要求或我们有特殊政策，否则已支付的费用不予退还</li>
              <li>我们有权调整价格，但会提前通知现有用户</li>
              <li>滥用付费功能（如退款欺诈）将导致账户封禁</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              账户终止
            </h2>
            <p className="text-slate-600 leading-relaxed mb-6">
              我们保留在以下情况下终止或暂停您账户的权利：违反服务条款、长期不活跃、
              法律要求或我们发现账户存在安全风险。账户终止后，相关数据将按隐私政策处理。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              条款修改
            </h2>
            <p className="text-slate-600 leading-relaxed mb-6">
              我们可能会不时更新这些条款。重大变更将通过邮件或网站公告通知您。
              继续使用服务即表示您接受修改后的条款。
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              联系我们
            </h2>
            <p className="text-slate-600 leading-relaxed">
              如有任何问题，请联系我们：
            </p>
            <p className="text-slate-600 mt-2">
              邮箱：terms@human.online
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
