const nextConfig = {
  reactStrictMode: true,
  compiler: {
    styledComponents: true,
    emotion: true,
  },
  experimental: {
    appDir: true,
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
              script-src 'self' 'unsafe-eval';
              style-src 'self' 'unsafe-inline';
              img-src 'self' data:;
              font-src 'self';
              connect-src 'self' ${process.env.NEXT_PUBLIC_SUPABASE_URL}
            `.replace(/\s+/g, ' ')
          }
        ]
      }
    ]
  }
}

module.exports = nextConfig 