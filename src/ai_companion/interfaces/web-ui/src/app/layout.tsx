import { Inter } from 'next/font/google';
import type { Metadata } from "next";
import AppProviders from '../components/providers/appproviders';
import ClientLayout from '../components/layout/ClientLayout';
import "./globals.css";

// Load Inter font
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

// Define metadata for the application
export const metadata: Metadata = {
  title: "AI Companion - Healthcare Assistance",
  description: "Interactive AI companion for healthcare assistance",
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
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={`${inter.variable} font-sans antialiased min-h-screen bg-gray-50`} suppressHydrationWarning>
        {/* Wrap the entire application with our providers */}
        <AppProviders>
          <ClientLayout>
            {children}
          </ClientLayout>
        </AppProviders>
      </body>
    </html>
  );
}
