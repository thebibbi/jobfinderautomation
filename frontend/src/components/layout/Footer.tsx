import React from 'react';
import Link from 'next/link';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="md:flex md:items-center md:justify-between">
          {/* Copyright */}
          <div className="flex justify-center md:order-2">
            <p className="text-center text-sm text-gray-500">
              &copy; {currentYear} Job Automation. All rights reserved.
            </p>
          </div>

          {/* Links */}
          <div className="mt-4 md:mt-0 md:order-1">
            <div className="flex justify-center space-x-6">
              <Link
                href="/about"
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                About
              </Link>
              <Link
                href="/privacy"
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Privacy
              </Link>
              <Link
                href="/terms"
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Terms
              </Link>
              <Link
                href="/help"
                className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Help
              </Link>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-400">
            Powered by AI-driven job automation technology
          </p>
        </div>
      </div>
    </footer>
  );
}
