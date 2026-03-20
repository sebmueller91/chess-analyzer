"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import type { Player } from "@/lib/api";
import Card from "./ui/Card";
import Badge from "./ui/Badge";
import Button from "./ui/Button";
import Modal from "./ui/Modal";

interface PlayerCardProps {
  player: Player;
  onDelete: (username: string) => Promise<void>;
  onReanalyze: (username: string) => Promise<void>;
}

function statusBadge(status: string) {
  switch (status) {
    case "complete":
      return <Badge variant="success">Complete</Badge>;
    case "analyzing":
      return <Badge variant="warning">Analyzing</Badge>;
    case "error":
      return <Badge variant="danger">Error</Badge>;
    default:
      return <Badge variant="neutral">Idle</Badge>;
  }
}

function statusDot(status: string) {
  switch (status) {
    case "complete":
      return "bg-chess-green";
    case "analyzing":
      return "bg-chess-gold animate-pulse";
    case "error":
      return "bg-chess-accent";
    default:
      return "bg-gray-500";
  }
}

export default function PlayerCard({
  player,
  onDelete,
  onReanalyze,
}: PlayerCardProps) {
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await onDelete(player.username);
      setDeleteOpen(false);
    } finally {
      setDeleting(false);
    }
  };

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      await onReanalyze(player.username);
    } finally {
      setReanalyzing(false);
    }
  };

  return (
    <>
      <Card className="group flex flex-col justify-between hover:border-chess-accent/30">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`h-2.5 w-2.5 rounded-full ${statusDot(player.status)}`} />
              <h3 className="text-lg font-bold text-white">{player.username}</h3>
            </div>
            {statusBadge(player.status)}
          </div>

          {player.status === "analyzing" && (
            <div className="mb-3">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-chess-surface-light">
                <div className="h-full animate-pulse rounded-full bg-chess-gold" style={{ width: "60%" }} />
              </div>
              <p className="mt-1 text-xs text-gray-400">Analyzing games...</p>
            </div>
          )}

          {player.error_message && (
            <p className="mb-3 text-xs text-chess-accent">{player.error_message}</p>
          )}

          <div className="mb-4 space-y-1 text-sm text-gray-400">
            <p>
              <span className="text-gray-500">Games:</span>{" "}
              <span className="text-gray-200">{player.games_analyzed}</span>
            </p>
            {player.time_control && (
              <p>
                <span className="text-gray-500">Time Control:</span>{" "}
                <span className="capitalize text-gray-200">{player.time_control}</span>
              </p>
            )}
            {player.last_analyzed_at && (
              <p>
                <span className="text-gray-500">Analyzed:</span>{" "}
                <span className="text-gray-200">
                  {new Date(player.last_analyzed_at).toLocaleDateString()}
                </span>
              </p>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          {player.status === "complete" && (
            <Button
              size="sm"
              onClick={() => router.push(`/player/${player.username}`)}
              className="flex-1"
            >
              Open
            </Button>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={handleReanalyze}
            loading={reanalyzing}
            disabled={player.status === "analyzing"}
          >
            ⟳
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setDeleteOpen(true)}>
            🗑
          </Button>
        </div>
      </Card>

      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete Player"
        confirmLabel="Delete"
        confirmVariant="primary"
        onConfirm={handleDelete}
        loading={deleting}
      >
        <p>
          Are you sure you want to delete <strong>{player.username}</strong>?
          This will remove all analysis data.
        </p>
      </Modal>
    </>
  );
}
