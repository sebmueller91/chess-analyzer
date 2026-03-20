"use client";

import { useState, useMemo } from "react";
import { Chessboard } from "react-chessboard";
import { Chess } from "chess.js";

interface MoveVisualizerProps {
  fen: string;
  playedMove: string;
  bestMove: string;
  evalBefore: number;
  evalAfter: number;
  playerColor: string;
  classification: string;
  motifLabel?: string;
}

type Tab = "position" | "played" | "best";

function getMoveSquares(
  fen: string,
  moveSan: string
): { from: string; to: string } | null {
  try {
    const game = new Chess(fen);
    const move = game.move(moveSan);
    if (!move) return null;
    return { from: move.from, to: move.to };
  } catch {
    return null;
  }
}

function getFenAfterMove(fen: string, moveSan: string): string | null {
  try {
    const game = new Chess(fen);
    const move = game.move(moveSan);
    if (!move) return null;
    return game.fen();
  } catch {
    return null;
  }
}

function formatEval(val: number): string {
  const sign = val > 0 ? "+" : "";
  return `${sign}${val.toFixed(1)}`;
}

export default function MoveVisualizer({
  fen,
  playedMove,
  bestMove,
  evalBefore,
  evalAfter,
  playerColor,
  classification,
  motifLabel,
}: MoveVisualizerProps) {
  const [activeTab, setActiveTab] = useState<Tab>("position");

  const playedSquares = useMemo(() => getMoveSquares(fen, playedMove), [fen, playedMove]);
  const bestSquares = useMemo(() => getMoveSquares(fen, bestMove), [fen, bestMove]);
  const fenAfterPlayed = useMemo(() => getFenAfterMove(fen, playedMove), [fen, playedMove]);
  const fenAfterBest = useMemo(() => getFenAfterMove(fen, bestMove), [fen, bestMove]);

  const canShowPlayed = playedSquares !== null && fenAfterPlayed !== null;
  const canShowBest = bestSquares !== null && fenAfterBest !== null;

  // Fall back to position tab if the active tab's move can't be parsed
  const effectiveTab =
    (activeTab === "played" && !canShowPlayed) ||
    (activeTab === "best" && !canShowBest)
      ? "position"
      : activeTab;

  const boardPosition =
    effectiveTab === "played"
      ? fenAfterPlayed!
      : effectiveTab === "best"
        ? fenAfterBest!
        : fen;

  const customSquareStyles =
    effectiveTab === "played" && playedSquares
      ? {
          [playedSquares.from]: { backgroundColor: "rgba(255, 80, 80, 0.6)" },
          [playedSquares.to]: { backgroundColor: "rgba(255, 80, 80, 0.6)" },
        }
      : effectiveTab === "best" && bestSquares
        ? {
            [bestSquares.from]: { backgroundColor: "rgba(80, 200, 120, 0.6)" },
            [bestSquares.to]: { backgroundColor: "rgba(80, 200, 120, 0.6)" },
          }
        : {};

  const orientation: "white" | "black" =
    playerColor === "black" ? "black" : "white";

  // Eval bar calculations (capped at ±10)
  const clampedBefore = Math.max(-10, Math.min(10, evalBefore));
  const whitePercent = ((clampedBefore + 10) / 20) * 100;
  const evalDiff = evalAfter - evalBefore;

  const classificationColor =
    classification === "blunder"
      ? "text-chess-accent"
      : classification === "mistake"
        ? "text-chess-gold"
        : "text-blue-400";

  const showMotif =
    motifLabel && motifLabel !== "Tactical oversight";

  const tabButtonClass = (tab: Tab) => {
    if (effectiveTab !== tab) return "bg-chess-dark text-gray-400";
    if (tab === "position") return "bg-chess-surface-light text-white";
    if (tab === "played") return "bg-red-900/50 text-red-300";
    return "bg-green-900/50 text-green-300";
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Motif badge */}
      {showMotif && (
        <span
          className={`inline-block self-start rounded-full px-2.5 py-0.5 text-xs font-medium ${classificationColor} border border-current/30 bg-current/10`}
        >
          {motifLabel}
        </span>
      )}

      {/* Tab buttons */}
      <div className="flex gap-1 rounded-lg bg-chess-dark p-1">
        <button
          onClick={() => setActiveTab("position")}
          className={`flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${tabButtonClass("position")}`}
        >
          Position
        </button>
        <button
          onClick={() => canShowPlayed && setActiveTab("played")}
          disabled={!canShowPlayed}
          className={`flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${tabButtonClass("played")} ${!canShowPlayed ? "opacity-40 cursor-not-allowed" : ""}`}
        >
          Played ❌
        </button>
        <button
          onClick={() => canShowBest && setActiveTab("best")}
          disabled={!canShowBest}
          className={`flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${tabButtonClass("best")} ${!canShowBest ? "opacity-40 cursor-not-allowed" : ""}`}
        >
          Best ✓
        </button>
      </div>

      {/* Chessboard */}
      <div className="rounded-lg overflow-hidden border border-chess-surface-light w-[280px]">
        <Chessboard
          options={{
            position: boardPosition,
            boardOrientation: orientation,
            allowDragging: false,
            squareStyles: customSquareStyles,
          }}
        />
      </div>

      {/* Eval bar */}
      <div className="flex flex-col gap-1">
        <div className="relative h-5 w-full overflow-hidden rounded-full border border-chess-surface-light bg-gray-700">
          <div
            className="absolute inset-y-0 left-0 bg-chess-cream transition-all duration-300"
            style={{ width: `${whitePercent}%` }}
          />
          <div className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-gray-800 mix-blend-difference">
            {formatEval(evalBefore)}
          </div>
        </div>
        <p className="text-center text-xs text-gray-400">
          {formatEval(evalBefore)} → {formatEval(evalAfter)}{" "}
          <span className={evalDiff < 0 ? "text-chess-accent" : "text-chess-green"}>
            ({formatEval(evalDiff)})
          </span>
        </p>
      </div>
    </div>
  );
}
