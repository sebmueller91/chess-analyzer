"use client";

import React from "react";
import type { Player } from "@/lib/api";
import PlayerCard from "./PlayerCard";

interface PlayerListProps {
  players: Player[];
  onDelete: (username: string) => Promise<void>;
  onReanalyze: (username: string) => Promise<void>;
}

export default function PlayerList({
  players,
  onDelete,
  onReanalyze,
}: PlayerListProps) {
  if (players.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-chess-surface-light p-12 text-center">
        <p className="text-lg text-gray-500">♟ No players analyzed yet.</p>
        <p className="mt-1 text-sm text-gray-600">
          Enter a username above to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {players.map((player) => (
        <PlayerCard
          key={player.username}
          player={player}
          onDelete={onDelete}
          onReanalyze={onReanalyze}
        />
      ))}
    </div>
  );
}
