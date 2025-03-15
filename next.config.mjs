/**
 * @type {import('next').NextConfig}
 */
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

// Get __dirname equivalent in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const nextConfig = {
  /* config options here */
  experimental: {
    esmExternals: 'loose', // This helps with ESM compatibility
  },
  webpack: (config, { isServer }) => {
    // Add support for path aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': resolve(__dirname, './src'),
    };
    
    // Add specific module resolution paths
    config.resolve.modules = [
      resolve(__dirname, './src'),
      resolve(__dirname, './node_modules'),
      'node_modules',
      ...(config.resolve.modules || []),
    ];
    
    return config;
  },
  // Ensure Next.js uses the src directory
  distDir: '.next',
  reactStrictMode: true,
};

export default nextConfig; 