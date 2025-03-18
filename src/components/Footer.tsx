import React from 'react';

export default function Footer() {
  return (
    <footer className="py-4 px-6 text-center text-sm text-gray-500 border-t border-gray-200">
      <div className="container mx-auto">
        © {new Date().getFullYear()} Trainer&apos;s Memory. All rights reserved.
      </div>
    </footer>
  );
} 