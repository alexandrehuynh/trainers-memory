'use client';

import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  title?: string;
  className?: string;
  footer?: ReactNode;
}

export default function Card({ children, title, className = '', footer }: CardProps) {
  return (
    <div className={`card rounded-lg border shadow-sm overflow-hidden ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-medium">{title}</h3>
        </div>
      )}
      <div className="px-6 py-5">{children}</div>
      {footer && <div className="px-6 py-4 border-t">{footer}</div>}
    </div>
  );
} 