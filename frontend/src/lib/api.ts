const API_BASE = "";

export interface Player {
  username: string;
  last_analyzed_at: string | null;
  games_analyzed: number;
  time_control: string | null;
  status: string;
  error_message: string | null;
}

export interface AnalysisStatus {
  username: string;
  status: string;
  progress: {
    games_fetched: number;
    games_analyzed: number;
  };
}

export interface MistakeExample {
  game_opponent: string;
  game_date: string;
  move_number: number;
  phase: string;
  played_move: string;
  best_move: string;
  eval_before: number;
  eval_after: number;
  fen: string;
  classification: string;
  opening_name: string;
  player_color: string;
  result: string;
  motif?: string;
  motif_label?: string;
}

export interface Weakness {
  name: string;
  description: string;
  frequency: number;
  severity: string;
  phase: string;
  examples: unknown[];
}

export interface Opening {
  name: string;
  eco: string;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  avg_accuracy: number;
}

export interface PhaseStats {
  mistakes: number;
  inaccuracies: number;
  blunders: number;
  avg_accuracy: number;
}

export interface ColorStats {
  games: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  avg_accuracy: number;
}

export interface Report {
  username: string;
  summary: {
    total_games: number;
    wins: number;
    losses: number;
    draws: number;
    win_rate: number;
    avg_accuracy: number;
  };
  top_weaknesses: Weakness[];
  openings: Opening[];
  phase_distribution: {
    opening: PhaseStats;
    middlegame: PhaseStats;
    endgame: PhaseStats;
  };
  color_comparison: {
    white: ColorStats;
    black: ColorStats;
  };
  mistake_examples: MistakeExample[];
  training_recommendations: {
    title: string;
    description: string;
    priority: string;
    related_weakness: string;
  }[];
  coaching_summary: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "Unknown error");
    throw new ApiError(body, res.status);
  }
  return res.json();
}

export async function fetchPlayers(): Promise<Player[]> {
  const data = await request<{ players: Player[] }>("/api/players");
  return data.players;
}

export async function startAnalysis(
  username: string,
  timeControl: string,
  gameCount: number
): Promise<void> {
  await request("/api/analyze", {
    method: "POST",
    body: JSON.stringify({
      username,
      time_control: timeControl || undefined,
      game_count: gameCount,
    }),
  });
}

export async function getAnalysisStatus(
  username: string
): Promise<AnalysisStatus> {
  return request<AnalysisStatus>(`/api/status/${encodeURIComponent(username)}`);
}

export async function getReport(username: string): Promise<Report> {
  return request<Report>(`/api/reports/${encodeURIComponent(username)}`);
}

export async function deletePlayer(username: string): Promise<void> {
  await request(`/api/players/${encodeURIComponent(username)}`, {
    method: "DELETE",
  });
}

export async function reanalyzePlayer(
  username: string,
  timeControl: string,
  gameCount: number
): Promise<void> {
  const params = new URLSearchParams({
    time_control: timeControl || "all",
    game_count: String(gameCount),
  });
  await request(
    `/api/players/${encodeURIComponent(username)}/reanalyze?${params}`,
    { method: "POST" }
  );
}

export async function sendChatMessage(
  username: string,
  message: string
): Promise<string> {
  const data = await request<{ response: string }>(
    "/api/chat",
    {
      method: "POST",
      body: JSON.stringify({ username, message }),
    }
  );
  return data.response;
}

export async function clearChat(username: string): Promise<void> {
  await request(`/api/chat/${encodeURIComponent(username)}`, {
    method: "DELETE",
  });
}
