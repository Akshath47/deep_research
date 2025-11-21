"use client";

import { useState } from "react";
import { PromptState } from "@/components/states/prompt-state";
import { ProcessState } from "@/components/states/process-state";
import { ResultState } from "@/components/states/result-state";

export type UIState = "prompt" | "process" | "result";

export interface AgentMetadata {
  name: string;
  display_name: string;
  description: string;
  icon: string;
  order: number;
}

export interface ResearchStatus {
  thread_id: string;
  status: "queued" | "running" | "completed" | "error";
  current_agent: string | null;
  progress_percentage: number | null;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface ResearchResult {
  thread_id: string;
  status: string;
  report: string;
  subqueries: string[];
  citations: Array<{ file: string; content: string }>;
  files: Record<string, string>;
  metadata: {
    started_at: string;
    completed_at: string;
    total_time: string;
  };
}

export default function ResearchInterface() {
  const [uiState, setUIState] = useState<UIState>("prompt");
  const [query, setQuery] = useState<string>("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);

  const handleStartResearch = (searchQuery: string, researchThreadId: string) => {
    setQuery(searchQuery);
    setThreadId(researchThreadId);
    setUIState("process");
  };

  const handleResearchComplete = (researchResult: ResearchResult) => {
    setResult(researchResult);
    setUIState("result");
  };

  const handleNewSearch = () => {
    setQuery("");
    setThreadId(null);
    setResult(null);
    setUIState("prompt");
  };

  return (
    <div className="min-h-screen bg-background">
      {uiState === "prompt" && (
        <PromptState onStartResearch={handleStartResearch} />
      )}

      {uiState === "process" && threadId && (
        <ProcessState
          query={query}
          threadId={threadId}
          onComplete={handleResearchComplete}
        />
      )}

      {uiState === "result" && result && (
        <ResultState result={result} onNewSearch={handleNewSearch} />
      )}
    </div>
  );
}
