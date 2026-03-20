"use client";

import React from "react";

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export default function Card({ title, children, className = "", icon }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-chess-surface-light bg-chess-surface/80 p-5 shadow-lg backdrop-blur-sm transition-colors duration-200 ${className}`}
    >
      {title && (
        <div className="mb-4 flex items-center gap-2">
          {icon && <span className="text-chess-gold">{icon}</span>}
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
      )}
      {children}
    </div>
  );
}
