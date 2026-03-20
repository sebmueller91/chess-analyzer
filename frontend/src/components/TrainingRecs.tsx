"use client";

import React from "react";
import Card from "./ui/Card";
import Badge from "./ui/Badge";

interface TrainingRec {
  title: string;
  description: string;
  priority: string;
  related_weakness: string;
}

interface TrainingRecsProps {
  recommendations: TrainingRec[];
}

function priorityVariant(p: string): "danger" | "warning" | "success" {
  switch (p.toLowerCase()) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    default:
      return "success";
  }
}

export default function TrainingRecs({ recommendations }: TrainingRecsProps) {
  if (recommendations.length === 0) {
    return (
      <Card title="Training Recommendations" icon={<span>📚</span>}>
        <p className="text-gray-400">No recommendations available yet.</p>
      </Card>
    );
  }

  return (
    <Card title="Training Recommendations" icon={<span>📚</span>}>
      <div className="space-y-3">
        {recommendations.map((rec, i) => (
          <div
            key={i}
            className="rounded-lg border border-chess-surface-light bg-chess-dark/50 p-4"
          >
            <div className="mb-2 flex items-start justify-between gap-2">
              <h4 className="font-semibold text-white">{rec.title}</h4>
              <Badge variant={priorityVariant(rec.priority)}>
                {rec.priority}
              </Badge>
            </div>
            <p className="mb-2 text-sm text-gray-400">{rec.description}</p>
            {rec.related_weakness && (
              <p className="text-xs text-gray-500">
                Related: <span className="text-chess-gold">{rec.related_weakness}</span>
              </p>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
