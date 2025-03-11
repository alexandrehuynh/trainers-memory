'use client';

import { ReactNode } from 'react';
import { useTheme } from '@/lib/themeContext';

interface CardProps {
  children: ReactNode;
  title?: string;
  className?: string;
  footer?: ReactNode;
}

export default function Card({ children, title, className = '', footer }: CardProps) {
  const { theme } = useTheme();
  
  return (
    <div className={`card rounded-lg border ${theme === 'light' ? 'bg-white border-gray-200' : 'bg-gray-800 border-gray-700'} shadow-sm overflow-hidden ${className}`}>
      {title && (
        <div className={`px-6 py-4 ${theme === 'light' ? 'border-gray-200' : 'border-gray-700'} border-b`}>
          <h3 className={`text-lg font-medium ${theme === 'light' ? 'text-gray-800' : 'text-gray-100'}`}>{title}</h3>
        </div>
      )}
      <div className="px-6 py-5">{children}</div>
      {footer && <div className={`px-6 py-4 ${theme === 'light' ? 'border-gray-200' : 'border-gray-700'} border-t`}>{footer}</div>}
    </div>
  );
} 