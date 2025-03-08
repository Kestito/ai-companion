/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
  },
  experimental: {
    // Enable if you're using App Router
    // appDir: true,
  },
  compiler: {
    styledComponents: true,
    emotion: true,
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: `
              default-src 'self' ${process.env.NEXT_PUBLIC_SUPABASE_URL};
              script-src 'self' 'unsafe-inline' 'unsafe-eval';
              style-src 'self' 'unsafe-inline';
              img-src 'self' data:;
              connect-src 'self' ${process.env.NEXT_PUBLIC_SUPABASE_URL};
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