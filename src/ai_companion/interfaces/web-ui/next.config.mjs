/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,
  
  // Add environmental variables to be available in the browser
  env: {
    NEXT_PUBLIC_SUPABASE_URL: 'https://aubulhjfeszmsheonmpy.supabase.co',
    NEXT_PUBLIC_SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1YnVsaGpmZXN6bXNoZW9ubXB5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTI4NzQxMiwiZXhwIjoyMDUwODYzNDEyfQ.aI0lG4QDWytCV5V0BLK6Eus8fXqUgTiTuDa7kqpCCkc'
  },
  
  // Configure redirects, rewrites, etc.
  async redirects() {
    return [];
  },
  
  // Configure webpack if needed
  webpack(config, { dev, isServer }) {
    return config;
  },
};

export default nextConfig; 