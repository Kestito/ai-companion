import { Inter } from 'next/font/google';
import type { Metadata } from "next";
import "./globals.css";
import { Providers } from './providers';
import AuthProvider from "@/components/AuthProvider";
import logger from '../utils/logger';
import ClientLayout from '@/components/layout/ClientLayout';

// Load Inter font
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

// Configure logger for the application
logger.configureLogger({
  applicationName: 'ai-companion',
  enableRemote: process.env.NODE_ENV === 'production',
  minLevel: process.env.NODE_ENV === 'production' ? 1 : 0, // INFO in prod, DEBUG in dev
});

// Define metadata for the application
export const metadata: Metadata = {
  title: "AI Companion",
  description: "Your AI Companion App",
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/icon.ico', sizes: 'any' }
    ],
  },
};

/**
 * Root layout component for the application
 * Wraps all pages with necessary providers and global styles
 * 
 * @param children - The page content
 * @returns The layout wrapped page
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Log application startup
  logger.info('Application starting', {
    environment: process.env.NODE_ENV,
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  });

  // Setup global error boundary
  const handleError = (error: Error) => {
    logger.error('Unhandled error in application', error, {
      location: 'RootLayout',
    });
  };

  if (typeof window !== 'undefined') {
    window.onerror = (message, source, lineno, colno, error) => {
      handleError(error || new Error(String(message)));
    };

    window.onunhandledrejection = (event) => {
      handleError(event.reason);
    };
  }

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className={`${inter.variable} font-sans antialiased min-h-screen bg-gray-50`} suppressHydrationWarning>
        <AuthProvider>
          <Providers>
            <ClientLayout>
              {children}
            </ClientLayout>
          </Providers>
        </AuthProvider>
      </body>
    </html>
  );
}
