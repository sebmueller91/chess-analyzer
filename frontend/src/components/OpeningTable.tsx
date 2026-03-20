"use client";

import React, { useState, useMemo } from "react";
import Card from "./ui/Card";
import type { Opening } from "@/lib/api";

interface OpeningTableProps {
  openings: Opening[];
}

type SortKey = "name" | "games_played" | "win_rate" | "avg_accuracy";
type SortDir = "asc" | "desc";

export default function OpeningTable({ openings }: OpeningTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("games_played");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [showAll, setShowAll] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...openings];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string" && typeof bv === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortDir === "asc"
        ? (av as number) - (bv as number)
        : (bv as number) - (av as number);
    });
    return copy;
  }, [openings, sortKey, sortDir]);

  const displayed = showAll ? sorted : sorted.slice(0, 10);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const arrow = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " ↑" : " ↓") : "";

  return (
    <Card title="Opening Performance" icon={<span>📖</span>}>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-chess-surface-light text-gray-400">
              <th
                className="cursor-pointer px-3 py-2 hover:text-white"
                onClick={() => toggleSort("name")}
              >
                Opening{arrow("name")}
              </th>
              <th className="px-3 py-2">ECO</th>
              <th
                className="cursor-pointer px-3 py-2 hover:text-white"
                onClick={() => toggleSort("games_played")}
              >
                Games{arrow("games_played")}
              </th>
              <th
                className="cursor-pointer px-3 py-2 hover:text-white"
                onClick={() => toggleSort("win_rate")}
              >
                Win Rate{arrow("win_rate")}
              </th>
              <th
                className="cursor-pointer px-3 py-2 hover:text-white"
                onClick={() => toggleSort("avg_accuracy")}
              >
                Accuracy{arrow("avg_accuracy")}
              </th>
              <th className="px-3 py-2">W / L / D</th>
            </tr>
          </thead>
          <tbody>
            {displayed.map((o, i) => (
              <tr
                key={o.eco + o.name}
                className={`border-b border-chess-surface-light/50 transition-colors hover:bg-chess-surface-light/30 ${
                  i % 2 === 0 ? "bg-chess-surface/50" : ""
                }`}
              >
                <td className="px-3 py-2.5 font-medium text-white">
                  {o.name}
                </td>
                <td className="px-3 py-2.5 text-gray-400">{o.eco}</td>
                <td className="px-3 py-2.5">{o.games_played}</td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-chess-surface-light">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${o.win_rate}%`,
                          backgroundColor:
                            o.win_rate >= 55
                              ? "#4ade80"
                              : o.win_rate >= 45
                                ? "#f5c842"
                                : "#e94560",
                        }}
                      />
                    </div>
                    <span className="text-xs">{o.win_rate.toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-12 overflow-hidden rounded-full bg-chess-surface-light">
                      <div
                        className="h-full rounded-full bg-blue-400"
                        style={{ width: `${o.avg_accuracy}%` }}
                      />
                    </div>
                    <span className="text-xs">{o.avg_accuracy.toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-3 py-2.5 text-xs text-gray-400">
                  <span className="text-chess-green">{o.wins}</span>
                  {" / "}
                  <span className="text-chess-accent">{o.losses}</span>
                  {" / "}
                  <span className="text-gray-400">{o.draws}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sorted.length > 10 && (
        <button
          className="mt-3 w-full text-center text-sm text-chess-accent hover:underline"
          onClick={() => setShowAll(!showAll)}
        >
          {showAll ? "Show less" : `Show all ${sorted.length} openings`}
        </button>
      )}
    </Card>
  );
}
