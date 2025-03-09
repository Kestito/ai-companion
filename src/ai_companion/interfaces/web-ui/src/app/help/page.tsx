import React from 'react';

export default function HelpPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6">
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-8 max-w-2xl w-full text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">Help</h1>
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6">Support Center</h2>
        
        <div className="p-4 mb-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md">
          <p className="text-amber-700 dark:text-amber-400 font-medium">
            ⚠️ This feature is currently under development
          </p>
        </div>
        
        <p className="text-gray-600 dark:text-gray-300">
          The help section will provide comprehensive documentation, user guides, 
          FAQs, and support resources to assist with using the platform effectively.
        </p>
      </div>
    </div>
  );
} 