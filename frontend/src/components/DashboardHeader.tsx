"use client";

import React from "react";
import { useRouter } from "next/navigation";
import Badge from "./ui/Badge";
import Button from "./ui/Button";

interface DashboardHeaderProps {
  username: string;
  gamesAnalyzed: number;
  lastAnalyzed?: string;
  timeControl?: string;
  onReanalyze: () => void;
  reanalyzing: boolean;
}

export default function DashboardHeader({
  username,
  gamesAnalyzed,
  lastAnalyzed,
  timeControl,
  onReanalyze,
  reanalyzing,
}: DashboardHeaderProps) {
  const router = useRouter();

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          ← All Players
        </Button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{username}</h1>
            <Badge variant="success">Complete</Badge>
          </div>
          <div className="mt-1 flex items-center gap-3 text-sm text-gray-400">
            <span>{gamesAnalyzed} games analyzed</span>
            {timeControl && (
              <span className="capitalize">• {timeControl}</span>
            )}
            {lastAnalyzed && (
              <span>• {new Date(lastAnalyzed).toLocaleDateString()}</span>
            )}
          </div>
        </div>
      </div>
      <Button
        variant="secondary"
        onClick={onReanalyze}
        loading={reanalyzing}
      >
        ⟳ Re-analyze
      </Button>
    </div>
  );
}
