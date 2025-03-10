'use client';

import { useEffect } from 'react';
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider, useAuth } from "@/lib/authContext";
import { ThemeProvider } from "@/lib/themeContext";
import Navigation from '@/components/Navigation';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Trainer's Memory",
  description: "A fitness trainer's assistant application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased light-theme bg-gray-50 min-h-screen`}
      >
        <AuthProvider>
          <ThemeProvider>
            <AppContent>{children}</AppContent>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

// Separate component to use auth context inside
function AppContent({ children }: { children: React.ReactNode }) {
  const { refreshToken } = useAuth();
  
  useEffect(() => {
    // Listen for token refresh events from the API client
    const handleTokenRefreshNeeded = () => {
      console.log('Token refresh needed, attempting refresh...');
      refreshToken()
        .then(success => {
          console.log('Token refresh result:', success ? 'success' : 'failed');
        })
        .catch(error => {
          console.error('Error during token refresh:', error);
        });
    };
    
    window.addEventListener('auth:token-refresh-needed', handleTokenRefreshNeeded);
    
    return () => {
      window.removeEventListener('auth:token-refresh-needed', handleTokenRefreshNeeded);
    };
  }, [refreshToken]);
  
  return (
    <div className="flex flex-col min-h-screen">
      <Navigation />
      <main className="flex-grow container mx-auto p-4 sm:p-6">
        {children}
      </main>
      <footer className="py-4 text-center text-sm text-gray-500">
        © {new Date().getFullYear()} Trainer's Memory
      </footer>
    </div>
  );
}
