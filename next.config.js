/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    // More specific and complete alias configuration
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
      '@/lib': path.resolve(__dirname, 'src/lib'),
      '@/components': path.resolve(__dirname, 'src/components'),
      '@/app': path.resolve(__dirname, 'src/app'),
    };
    
    // Enhanced module resolution
    config.resolve.modules = [
      path.resolve(__dirname, 'src'),
      'node_modules',
      ...(config.resolve.modules || []),
    ];
    
    return config;
  },
  // Explicitly define routes to ensure they're recognized
  async rewrites() {
    return [
      {
        source: '/signin',
        destination: '/signin',
      },
      {
        source: '/login',
        destination: '/login',
      },
    ];
  },
};

module.exports = nextConfig; 