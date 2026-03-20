"use client";

import React from "react";
import Card from "./ui/Card";

interface CoachingSummaryProps {
  summary: string;
  loading?: boolean;
}

export default function CoachingSummary({
  summary,
  loading,
}: CoachingSummaryProps) {
  return (
    <Card title="Coaching Summary" icon={<span>🎓</span>}>
      {loading ? (
        <div className="space-y-3">
          <div className="h-4 w-full animate-pulse rounded bg-chess-surface-light" />
          <div className="h-4 w-5/6 animate-pulse rounded bg-chess-surface-light" />
          <div className="h-4 w-4/6 animate-pulse rounded bg-chess-surface-light" />
        </div>
      ) : summary ? (
        <div className="space-y-3 text-sm leading-relaxed text-gray-300">
          {summary.split("\n").map((paragraph, i) =>
            paragraph.trim() ? (
              <p key={i}>{paragraph}</p>
            ) : null
          )}
        </div>
      ) : (
        <p className="text-gray-400">
          No coaching summary available yet. Run an analysis to generate one.
        </p>
      )}
    </Card>
  );
}
