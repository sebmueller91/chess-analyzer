"use client";

import React from "react";
import Card from "./ui/Card";
import type { Report } from "@/lib/api";

interface StatsOverviewProps {
  summary: Report["summary"];
  phaseDistribution: Report["phase_distribution"];
}

function worstPhase(pd: Report["phase_distribution"]): string {
  const phases = [
    { name: "Opening", total: pd.opening.mistakes + pd.opening.blunders },
    { name: "Middlegame", total: pd.middlegame.mistakes + pd.middlegame.blunders },
    { name: "Endgame", total: pd.endgame.mistakes + pd.endgame.blunders },
  ];
  phases.sort((a, b) => b.total - a.total);
  return phases[0].name;
}

function winRateColor(rate: number): string {
  if (rate >= 60) return "text-chess-green";
  if (rate >= 45) return "text-chess-gold";
  return "text-chess-accent";
}

function accuracyColor(acc: number): string {
  if (acc >= 80) return "text-chess-green";
  if (acc >= 65) return "text-chess-gold";
  return "text-chess-accent";
}

export default function StatsOverview({
  summary,
  phaseDistribution,
}: StatsOverviewProps) {
  const stats = [
    {
      label: "Total Games",
      value: summary.total_games,
      icon: "♟",
      color: "text-white",
    },
    {
      label: "Win Rate",
      value: `${summary.win_rate.toFixed(1)}%`,
      icon: "🏆",
      color: winRateColor(summary.win_rate),
    },
    {
      label: "Avg Accuracy",
      value: `${summary.avg_accuracy.toFixed(1)}%`,
      icon: "🎯",
      color: accuracyColor(summary.avg_accuracy),
    },
    {
      label: "Weakest Phase",
      value: worstPhase(phaseDistribution),
      icon: "⚠",
      color: "text-chess-gold",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((s) => (
        <Card key={s.label} className="text-center">
          <div className="mb-1 text-2xl">{s.icon}</div>
          <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
          <div className="mt-1 text-xs text-gray-400">{s.label}</div>
        </Card>
      ))}
    </div>
  );
}
