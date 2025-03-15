/** @type {import('next').NextConfig} */

const path = require('path');

const nextConfig = {
  /* config options here */
  experimental: {
    // Empty but kept for structure
  },
  webpack: (config, { isServer }) => {
    // Add support for path aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, './src'),
    };
    
    // Add specific module resolution paths
    config.resolve.modules = [
      path.resolve(__dirname, './src'),
      path.resolve(__dirname, './node_modules'),
      'node_modules',
      ...(config.resolve.modules || []),
    ];
    
    // Add fallbacks for node modules
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      path: false,
      os: false,
    };

    // Ensure proper module extensions are recognized
    config.resolve.extensions = [
      '.js', '.jsx', '.ts', '.tsx', '.json', '.mjs', '.cjs',
      ...(config.resolve.extensions || [])
    ];
    
    return config;
  },
  // Ensure Next.js uses the src directory
  distDir: '.next',
  reactStrictMode: true,
};

module.exports = nextConfig; 