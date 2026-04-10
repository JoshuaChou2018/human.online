/** @type {import('next').NextConfig} */

// 从环境变量读取后端 API 地址，默认使用 localhost
// 格式: http://域名:端口 （不带 /api/v1 后缀）
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// 提取域名用于图片配置
const getDomain = (url) => {
  try {
    return new URL(url).hostname;
  } catch {
    return 'localhost';
  }
};

const apiDomain = getDomain(API_BASE_URL);

const nextConfig = {
  // 开发模式下可以禁用以提升性能（生产环境建议开启）
  reactStrictMode: process.env.NODE_ENV === 'production',
  
  // SWC 压缩（保持开启）
  swcMinify: true,
  
  // 图片优化配置
  images: {
    domains: ['localhost', apiDomain],
    // 禁用图片优化（开发模式可加速，但会丢失图片优化功能）
    unoptimized: process.env.NODE_ENV !== 'production',
  },
  
  // 实验性功能：模块化编译（提升启动速度）
  experimental: {
    // 并行编译
    parallelServerCompiles: true,
    parallelServerBuildTraces: true,
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_BASE_URL}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
