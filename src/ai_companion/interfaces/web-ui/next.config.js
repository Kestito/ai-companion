/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  // Add the environment variables here for build time
  env: {
    NEXT_PUBLIC_SUPABASE_URL: 'https://aubulhjfeszmsheonmpy.supabase.co',
    NEXT_PUBLIC_SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc'
  },
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '',
        pathname: '/**',
      },
    ],
  },
  experimental: {
    // Enable if you're using App Router
    // appDir: true,
  },
  compiler: {
    styledComponents: true,
    emotion: true,
  },
  // Ignore the punycode deprecation warning
  onDemandEntries: {
    // period (in ms) where the server will keep pages in the buffer
    maxInactiveAge: 25 * 1000,
    // number of pages that should be kept simultaneously without being disposed
    pagesBufferLength: 2,
  },
  async headers() {
    // Get API URL from env or use a default value for development
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    // Include the specific Azure Container App URL
    const azureContainerAppUrl = 'https://backend-app.redstone-957fece8.eastus.azurecontainerapps.io';
    // Hardcoded Supabase URL
    const supabaseUrl = 'https://aubulhjfeszmsheonmpy.supabase.co';
    
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: `
              default-src 'self' ${supabaseUrl};
              script-src 'self' 'unsafe-inline' 'unsafe-eval';
              style-src 'self' 'unsafe-inline';
              img-src 'self' data:;
              connect-src 'self' ${supabaseUrl} ${apiUrl} ${azureContainerAppUrl} https://*.azure.com https://*.azurecontainerapps.io https://*.azure.io;
              frame-src 'self';
              form-action 'self';
            `.replace(/\n/g, ' ')
          }
        ]
      }
    ]
  }
}

module.exports = nextConfig