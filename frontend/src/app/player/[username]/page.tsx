"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getReport,
  reanalyzePlayer,
  type Report,
  type MistakeExample,
} from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import DashboardHeader from "@/components/DashboardHeader";
import StatsOverview from "@/components/StatsOverview";
import WeaknessCard from "@/components/WeaknessCard";
import OpeningTable from "@/components/OpeningTable";
import PhaseChart from "@/components/PhaseChart";
import ColorComparison from "@/components/ColorComparison";
import MistakeExamples from "@/components/MistakeExamples";
import TrainingRecs from "@/components/TrainingRecs";
import CoachingSummary from "@/components/CoachingSummary";
import ChatPanel from "@/components/ChatPanel";

export default function PlayerDashboard() {
  const params = useParams<{ username: string }>();
  const username = params.username;

  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reanalyzing, setReanalyzing] = useState(false);
  const [chatMessage, setChatMessage] = useState<string | undefined>(undefined);

  const loadReport = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getReport(username);
      setReport(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load report"
      );
    } finally {
      setLoading(false);
    }
  }, [username]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      await reanalyzePlayer(username, "", 50);
    } catch {
      // Ignore reanalyze errors
    } finally {
      setReanalyzing(false);
    }
  };

  const handleExplainMistake = (mistake: MistakeExample) => {
    const msg = `Explain my mistake on move ${mistake.move_number} against ${mistake.game_opponent} where I played ${mistake.played_move} instead of ${mistake.best_move}. The position was in the ${mistake.phase} phase of a ${mistake.opening_name} game.`;
    setChatMessage(msg);
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Spinner size="lg" />
          <p className="text-gray-400">Loading analysis for {username}...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4">
          <div className="text-4xl">⚠️</div>
          <h2 className="text-xl font-semibold text-white">
            Report not found
          </h2>
          <p className="text-gray-400">
            {error || `No analysis data available for ${username}`}
          </p>
          <Link
            href="/"
            className="mt-4 rounded-lg bg-chess-accent px-4 py-2 text-white transition-colors hover:bg-chess-accent/85"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      {/* Header */}
      <DashboardHeader
        username={report.username}
        gamesAnalyzed={report.summary.total_games}
        onReanalyze={handleReanalyze}
        reanalyzing={reanalyzing}
      />

      {/* Main layout: 2 columns on desktop */}
      <div className="mt-6 flex flex-col gap-6 lg:flex-row">
        {/* Left column: analysis sections */}
        <div className="flex flex-col gap-6 lg:w-[65%]">
          <StatsOverview
            summary={report.summary}
            phaseDistribution={report.phase_distribution}
          />

          {/* Weaknesses */}
          {report.top_weaknesses.length > 0 && (
            <div>
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
                <span className="text-chess-gold">⚠</span> Top Weaknesses
              </h2>
              <div className="space-y-3">
                {report.top_weaknesses.map((w, i) => (
                  <WeaknessCard key={w.name} weakness={w} index={i} />
                ))}
              </div>
            </div>
          )}

          <OpeningTable openings={report.openings} />

          <PhaseChart phaseDistribution={report.phase_distribution} />

          <ColorComparison colorComparison={report.color_comparison} />

          <MistakeExamples
            mistakes={report.mistake_examples}
            onExplainMistake={handleExplainMistake}
          />

          <TrainingRecs recommendations={report.training_recommendations} />

          <CoachingSummary summary={report.coaching_summary} />
        </div>

        {/* Right column: chat panel (sticky on desktop) */}
        <div className="lg:w-[35%]">
          <div className="lg:sticky lg:top-20 lg:h-[calc(100vh-6rem)]">
            <ChatPanel
              username={username}
              initialMessage={chatMessage}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
