/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',
  
  async rewrites() {
    // Use environment variable for backend URL in production
    let backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    // Debug: Log the backend URL for troubleshooting
    console.log('🔍 Debug - Original BACKEND_URL:', process.env.BACKEND_URL);
    console.log('🔍 Debug - Processing backend URL:', backendUrl);
    
    // Ensure backend URL has proper protocol for Render deployment
    if (backendUrl && !backendUrl.startsWith('http://') && !backendUrl.startsWith('https://')) {
      // For Render, use https by default
      backendUrl = `https://${backendUrl}`;
    }
    
    // Handle potential trailing slash
    backendUrl = backendUrl.replace(/\/$/, '');
    
    // Additional validation
    if (!backendUrl || backendUrl === 'https://' || backendUrl === 'http://') {
      console.error('❌ Invalid BACKEND_URL detected, falling back to localhost');
      backendUrl = 'http://localhost:8000';
    }
    
    console.log('🔍 Debug - Final backend URL:', backendUrl);
    console.log('🔍 Debug - API rewrite: /api/:path* → ' + backendUrl + '/:path*');
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
  
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version' },
        ],
      },
    ];
  },
};

module.exports = nextConfig; 