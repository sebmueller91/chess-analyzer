"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import AnalysisForm from "@/components/AnalysisForm";
import PlayerList from "@/components/PlayerList";
import {
  fetchPlayers,
  startAnalysis,
  deletePlayer,
  reanalyzePlayer,
  type Player,
} from "@/lib/api";

export default function Home() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadPlayers = useCallback(async () => {
    try {
      const data = await fetchPlayers();
      setPlayers(data);
    } catch {
      // Silently fail on polling errors
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlayers();
    intervalRef.current = setInterval(loadPlayers, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [loadPlayers]);

  const handleAnalyze = async (
    username: string,
    timeControl: string,
    gameCount: number
  ) => {
    await startAnalysis(username, timeControl, gameCount);
    await loadPlayers();
  };

  const handleDelete = async (username: string) => {
    await deletePlayer(username);
    await loadPlayers();
  };

  const handleReanalyze = async (username: string) => {
    await reanalyzePlayer(username, "", 50);
    await loadPlayers();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Hero */}
      <section className="mb-12 text-center">
        <h1 className="mb-3 text-4xl font-bold text-white sm:text-5xl">
          Chess <span className="text-chess-accent">Analyzer</span>
        </h1>
        <p className="mx-auto max-w-xl text-lg text-gray-400">
          Analyze your Chess.com games, discover weaknesses, and get AI coaching
          to improve your play.
        </p>
      </section>

      {/* Analysis Form */}
      <section className="mx-auto mb-12 max-w-lg">
        <AnalysisForm onSubmit={handleAnalyze} />
      </section>

      {/* Analyzed Players */}
      <section>
        <h2 className="mb-6 flex items-center gap-2 text-xl font-semibold text-white">
          <span>📊</span> Analyzed Players
        </h2>
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-chess-accent border-t-transparent" />
          </div>
        ) : (
          <PlayerList
            players={players}
            onDelete={handleDelete}
            onReanalyze={handleReanalyze}
          />
        )}
      </section>
    </div>
  );
}
