/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  experimental: {
    esmExternals: 'loose', // This helps with ESM compatibility
  },
  webpack: (config) => {
    // Add support for path aliases
    config.resolve.alias = {
      ...config.resolve.alias,
    };
    return config;
  }
};

module.exports = nextConfig; 