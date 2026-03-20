"use client";

import React from "react";
import Card from "./ui/Card";
import Badge from "./ui/Badge";
import type { Weakness } from "@/lib/api";

interface WeaknessCardProps {
  weakness: Weakness;
  index: number;
}

function severityVariant(sev: string): "danger" | "warning" | "info" {
  switch (sev.toLowerCase()) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    default:
      return "info";
  }
}

function phaseVariant(phase: string): "info" | "warning" | "neutral" {
  switch (phase.toLowerCase()) {
    case "opening":
      return "info";
    case "middlegame":
      return "warning";
    default:
      return "neutral";
  }
}

const accentBorder: Record<string, string> = {
  high: "border-l-chess-accent",
  medium: "border-l-chess-gold",
  low: "border-l-blue-400",
};

export default function WeaknessCard({ weakness, index }: WeaknessCardProps) {
  const borderClass = accentBorder[weakness.severity.toLowerCase()] || "border-l-gray-500";

  return (
    <Card className={`border-l-4 ${borderClass}`}>
      <div className="mb-2 flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-chess-surface-light text-xs font-bold text-white">
            {index + 1}
          </span>
          <h4 className="font-semibold text-white">{weakness.name}</h4>
        </div>
        <div className="flex gap-1.5">
          <Badge variant={severityVariant(weakness.severity)}>
            {weakness.severity}
          </Badge>
          <Badge variant={phaseVariant(weakness.phase)}>
            {weakness.phase}
          </Badge>
        </div>
      </div>
      <p className="mb-3 text-sm text-gray-400">{weakness.description}</p>
      <div className="flex items-center gap-2">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-chess-surface-light">
          <div
            className="h-full rounded-full bg-chess-accent"
            style={{ width: `${Math.min(weakness.frequency * 100, 100)}%` }}
          />
        </div>
        <span className="text-xs font-medium text-gray-400">
          {(weakness.frequency * 100).toFixed(0)}% of games
        </span>
      </div>
    </Card>
  );
}
