import React from 'react';

interface ShellProps {
  children: React.ReactNode;
  sidebar: React.ReactNode;
}

export const Shell: React.FC<ShellProps> = ({ children, sidebar }) => {
  return (
    <div className="flex w-full h-screen overflow-hidden">
      {sidebar}
      <main className="flex-1 overflow-y-auto relative px-16 pt-10">
        {/* Asymmetrical Data Accent */}
        <div className="absolute top-0 right-0 w-[400px] h-full bg-gradient-to-l from-[#1c1b1b] to-transparent opacity-20 pointer-events-none" />
        <div className="relative z-10 max-w-5xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};
