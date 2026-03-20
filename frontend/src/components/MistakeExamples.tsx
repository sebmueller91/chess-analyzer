"use client";

import React from "react";
import Card from "./ui/Card";
import Badge from "./ui/Badge";
import Button from "./ui/Button";
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

export default function MistakeExamples({
  mistakes,
  onExplainMistake,
}: MistakeExamplesProps) {
  const displayed = mistakes.slice(0, 8);

  if (displayed.length === 0) {
    return (
      <Card title="Instructive Mistakes" icon={<span>💡</span>}>
        <p className="text-gray-400">No mistake examples available.</p>
      </Card>
    );
  }

  return (
    <Card title="Instructive Mistakes" icon={<span>💡</span>}>
      <div className="space-y-4">
        {displayed.map((m, i) => {
          const evalChange = `${m.eval_before >= 0 ? "+" : ""}${m.eval_before.toFixed(1)} → ${m.eval_after >= 0 ? "+" : ""}${m.eval_after.toFixed(1)}`;

          return (
            <div
              key={`${m.game_date}-${m.move_number}-${i}`}
              className="rounded-lg border border-chess-surface-light bg-chess-dark/50 p-4"
            >
              <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant={classificationVariant(m.classification)}>
                    {m.classification}
                  </Badge>
                  <span className="text-sm text-gray-400">Move {m.move_number}</span>
                  <Badge variant="neutral">{m.phase}</Badge>
                </div>
                <span className="text-xs text-gray-500">
                  vs {m.game_opponent} • {m.game_date}
                </span>
              </div>

              <div className="mb-2 text-sm text-gray-400">
                {m.opening_name} • Playing as{" "}
                <span className="capitalize text-gray-200">{m.player_color}</span>
                {" • "}{m.result}
              </div>

              <div className="mb-2 grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-gray-500">Played</div>
                  <div className={`font-mono font-medium ${classificationColor(m.classification)}`}>
                    {m.played_move}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Best move</div>
                  <div className="font-mono font-medium text-chess-green">
                    {m.best_move}
                  </div>
                </div>
              </div>

              <div className="mb-3 flex items-center gap-2">
                <span className="text-xs text-gray-500">Eval:</span>
                <span className="font-mono text-sm text-chess-accent">
                  {evalChange}
                </span>
              </div>

              <div className="mb-3 rounded border border-chess-surface-light bg-chess-surface p-2">
                <div className="text-xs text-gray-500">FEN</div>
                <div className="break-all font-mono text-xs text-gray-400">
                  {m.fen}
                </div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => onExplainMistake(m)}
              >
                💬 Explain this mistake
              </Button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
