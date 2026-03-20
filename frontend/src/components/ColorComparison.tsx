"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Card from "./ui/Card";
import type { Report } from "@/lib/api";

interface ColorComparisonProps {
  colorComparison: Report["color_comparison"];
}

export default function ColorComparison({
  colorComparison,
}: ColorComparisonProps) {
  const { white, black } = colorComparison;

  const barData = [
    { label: "Win Rate", White: white.win_rate, Black: black.win_rate },
    { label: "Accuracy", White: white.avg_accuracy, Black: black.avg_accuracy },
  ];

  return (
    <Card title="White vs Black" icon={<span>⚔</span>}>
      <div className="grid grid-cols-2 gap-6">
        {/* White side */}
        <div className="text-center">
          <div className="mb-2 text-3xl">♔</div>
          <h4 className="mb-3 font-semibold text-white">White</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Games</span>
              <span className="text-white">{white.games}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Win Rate</span>
              <span className="text-chess-green">{white.win_rate.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Accuracy</span>
              <span className="text-blue-400">{white.avg_accuracy.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Record</span>
              <span>
                <span className="text-chess-green">{white.wins}</span>
                {" / "}
                <span className="text-chess-accent">{white.losses}</span>
                {" / "}
                <span className="text-gray-400">{white.draws}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Black side */}
        <div className="text-center">
          <div className="mb-2 text-3xl">♚</div>
          <h4 className="mb-3 font-semibold text-white">Black</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Games</span>
              <span className="text-white">{black.games}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Win Rate</span>
              <span className="text-chess-green">{black.win_rate.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Accuracy</span>
              <span className="text-blue-400">{black.avg_accuracy.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Record</span>
              <span>
                <span className="text-chess-green">{black.wins}</span>
                {" / "}
                <span className="text-chess-accent">{black.losses}</span>
                {" / "}
                <span className="text-gray-400">{black.draws}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison bars */}
      <div className="mt-6 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={barData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              type="number"
              stroke="#94a3b8"
              fontSize={12}
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}%`}
            />
            <YAxis
              type="category"
              dataKey="label"
              stroke="#94a3b8"
              fontSize={12}
              width={70}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e293b",
                border: "1px solid #334155",
                borderRadius: "8px",
                color: "#e2e8f0",
              }}
              formatter={(value) => `${Number(value).toFixed(1)}%`}
            />
            <Bar dataKey="White" fill="#f0e6d3" radius={[0, 4, 4, 0]} barSize={16} />
            <Bar dataKey="Black" fill="#64748b" radius={[0, 4, 4, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
