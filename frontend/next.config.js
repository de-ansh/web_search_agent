/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Get backend URL from environment or default to localhost
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
  
  // Environment variables for the frontend
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
  
  // Enable experimental features if needed
  experimental: {
    // Add any experimental features here
  },
};

module.exports = nextConfig;