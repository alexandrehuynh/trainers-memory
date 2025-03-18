import { Metadata } from 'next';
import { ThemeProvider } from '@/lib/themeContext';
import { AuthProvider } from '@/lib/authContext';
import AppContent from '@/components/AppContent';
import './globals.css';

export const metadata: Metadata = {
  title: 'Trainer&apos;s Memory',
  description: 'A fitness trainer&apos;s assistant application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon_io/favicon.ico" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon_io/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon_io/favicon-16x16.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/favicon_io/apple-touch-icon.png" />
        <link rel="manifest" href="/favicon_io/site.webmanifest" />
      </head>
      <body className="min-h-screen">
        <AuthProvider>
          <ThemeProvider>
            <AppContent>
              {children}
            </AppContent>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
