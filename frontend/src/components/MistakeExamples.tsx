"use client";

import React, { useState, useCallback } from "react";
import Card from "./ui/Card";
import Badge from "./ui/Badge";
import Button from "./ui/Button";
import MoveVisualizer from "./MoveVisualizer";
import type { MistakeExample } from "@/lib/api";

interface MistakeExamplesProps {
  mistakes: MistakeExample[];
  onExplainMistake: (mistake: MistakeExample) => void;
}

function classificationVariant(c: string): "warning" | "danger" | "info" {
  switch (c.toLowerCase()) {
    case "blunder":
      return "danger";
    case "mistake":
      return "warning";
    default:
      return "info";
  }
}

function classificationColor(c: string): string {
  switch (c.toLowerCase()) {
    case "blunder":
      return "text-chess-accent";
    case "mistake":
      return "text-orange-400";
    default:
      return "text-chess-gold";
  }
}

function formatEval(val: number): string {
  return `${val >= 0 ? "+" : ""}${val.toFixed(1)}`;
}

export default function MistakeExamples({
  mistakes,
  onExplainMistake,
}: MistakeExamplesProps) {
  const displayed = mistakes.slice(0, 8);
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());

  const toggleCard = useCallback((index: number) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

  if (displayed.length === 0) {
    return (
      <Card title="Instructive Mistakes" icon={<span>💡</span>}>
        <p className="text-gray-400">No mistake examples available.</p>
      </Card>
    );
  }

  return (
    <Card title="Instructive Mistakes" icon={<span>💡</span>}>
      <div className="space-y-3">
        {displayed.map((m, i) => {
          const expanded = expandedCards.has(i);
          const evalChange = `${formatEval(m.eval_before)} → ${formatEval(m.eval_after)}`;
          const showMotif =
            m.motif_label && m.motif_label !== "Tactical oversight";

          return (
            <div
              key={`${m.game_date}-${m.move_number}-${i}`}
              className="rounded-lg border border-chess-surface-light bg-chess-dark/50 overflow-hidden"
            >
              {/* Collapsed header — always visible */}
              <button
                type="button"
                onClick={() => toggleCard(i)}
                className="flex w-full items-center gap-2 px-4 py-3 text-left transition-colors hover:bg-chess-surface/40"
              >
                <span className="text-xs text-gray-500 transition-transform duration-200"
                  style={{ display: "inline-block", transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}
                >
                  ▶
                </span>

                <Badge variant={classificationVariant(m.classification)}>
                  {m.classification}
                </Badge>

                {showMotif && (
                  <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-[10px] font-medium text-purple-300">
                    {m.motif_label}
                  </span>
                )}

                <span className="text-sm text-gray-400">Move {m.move_number}</span>

                <span className="mx-1 hidden text-gray-600 sm:inline">•</span>
                <span className="hidden text-xs text-gray-500 sm:inline">vs {m.game_opponent}</span>

                <span className="ml-auto flex items-center gap-3 text-xs">
                  <span className={`font-mono ${classificationColor(m.classification)}`}>
                    {m.played_move}
                  </span>
                  <span className="text-gray-600">→</span>
                  <span className="font-mono text-chess-green">{m.best_move}</span>
                  <span className="font-mono text-gray-500">{evalChange}</span>
                </span>
              </button>

              {/* Expanded content */}
              <div
                className="transition-all duration-200 ease-in-out"
                style={{
                  maxHeight: expanded ? "600px" : "0px",
                  opacity: expanded ? 1 : 0,
                  overflow: "hidden",
                }}
              >
                <div className="border-t border-chess-surface-light px-4 pb-4 pt-3">
                  <div className="mb-3 text-sm text-gray-400">
                    {m.opening_name} • Playing as{" "}
                    <span className="capitalize text-gray-200">{m.player_color}</span>
                    {" • "}{m.result} • {m.game_date}
                  </div>

                  <MoveVisualizer
                    fen={m.fen}
                    playedMove={m.played_move}
                    bestMove={m.best_move}
                    evalBefore={m.eval_before}
                    evalAfter={m.eval_after}
                    playerColor={m.player_color}
                    classification={m.classification}
                    motifLabel={m.motif_label}
                  />

                  <div className="mt-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onExplainMistake(m)}
                    >
                      💬 Explain this mistake
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
