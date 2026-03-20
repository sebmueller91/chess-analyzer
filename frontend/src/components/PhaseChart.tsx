"use client";

import React from "react";
import {
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from "recharts";
import Card from "./ui/Card";
import type { Report } from "@/lib/api";

interface PhaseChartProps {
  phaseDistribution: Report["phase_distribution"];
}

export default function PhaseChart({ phaseDistribution }: PhaseChartProps) {
  const data = [
    {
      phase: "Opening",
      Inaccuracies: phaseDistribution.opening.inaccuracies,
      Mistakes: phaseDistribution.opening.mistakes,
      Blunders: phaseDistribution.opening.blunders,
      Accuracy: phaseDistribution.opening.avg_accuracy,
    },
    {
      phase: "Middlegame",
      Inaccuracies: phaseDistribution.middlegame.inaccuracies,
      Mistakes: phaseDistribution.middlegame.mistakes,
      Blunders: phaseDistribution.middlegame.blunders,
      Accuracy: phaseDistribution.middlegame.avg_accuracy,
    },
    {
      phase: "Endgame",
      Inaccuracies: phaseDistribution.endgame.inaccuracies,
      Mistakes: phaseDistribution.endgame.mistakes,
      Blunders: phaseDistribution.endgame.blunders,
      Accuracy: phaseDistribution.endgame.avg_accuracy,
    },
  ];

  return (
    <Card title="Mistakes by Game Phase" icon={<span>📊</span>}>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="phase" stroke="#94a3b8" fontSize={12} />
            <YAxis yAxisId="left" stroke="#94a3b8" fontSize={12} />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#94a3b8"
              fontSize={12}
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "8px",
                color: "#e2e8f0",
              }}
            />
            <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
            <Bar
              yAxisId="left"
              dataKey="Inaccuracies"
              stackId="errors"
              fill="#f5c842"
              radius={[0, 0, 0, 0]}
            />
            <Bar
              yAxisId="left"
              dataKey="Mistakes"
              stackId="errors"
              fill="#f97316"
            />
            <Bar
              yAxisId="left"
              dataKey="Blunders"
              stackId="errors"
              fill="#e94560"
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="Accuracy"
              stroke="#4ade80"
              strokeWidth={2}
              dot={{ fill: "#4ade80", r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
