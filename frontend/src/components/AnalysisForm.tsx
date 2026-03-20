"use client";

import React, { useState } from "react";
import Input from "./ui/Input";
import Select from "./ui/Select";
import Button from "./ui/Button";
import Card from "./ui/Card";

interface AnalysisFormProps {
  onSubmit: (username: string, timeControl: string, gameCount: number) => Promise<void>;
}

const TIME_CONTROLS = [
  { value: "", label: "All" },
  { value: "rapid", label: "Rapid" },
  { value: "blitz", label: "Blitz" },
  { value: "bullet", label: "Bullet" },
];

const GAME_COUNTS = [
  { value: "20", label: "20 games" },
  { value: "50", label: "50 games" },
  { value: "100", label: "100 games" },
];

export default function AnalysisForm({ onSubmit }: AnalysisFormProps) {
  const [username, setUsername] = useState("");
  const [timeControl, setTimeControl] = useState("");
  const [gameCount, setGameCount] = useState("50");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const trimmed = username.trim();
    if (trimmed.length < 3) {
      setError("Username must be at least 3 characters");
      return;
    }
    setLoading(true);
    try {
      await onSubmit(trimmed, timeControl, parseInt(gameCount));
      setUsername("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Analyze Your Games" icon={<span>🔍</span>}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Chess.com Username"
          placeholder="e.g. hikaru"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          error={error}
          icon={<span>♟</span>}
        />
        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Time Control"
            options={TIME_CONTROLS}
            value={timeControl}
            onChange={(e) => setTimeControl(e.target.value)}
          />
          <Select
            label="Number of Games"
            options={GAME_COUNTS}
            value={gameCount}
            onChange={(e) => setGameCount(e.target.value)}
          />
        </div>
        <Button type="submit" loading={loading} size="lg" fullWidth>
          🔍 Analyze
        </Button>
      </form>
    </Card>
  );
}
