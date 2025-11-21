"use client";

import { useEffect, useState, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Split,
  Target,
  Users,
  CheckCircle,
  FileText,
  Eye,
  Loader2,
  CheckCircle2
} from "lucide-react";
import { ResearchResult } from "@/components/research-interface";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ProcessStateProps {
  query: string;
  threadId: string;
  onComplete: (result: ResearchResult) => void;
}

interface AgentEvent {
  type: string;
  timestamp: string;
  agent: string;
  agent_display_name: string;
  agent_description: string;
  status: string;
}

const AGENT_ICONS: Record<string, any> = {
  clarifier: Search,
  decomposer: Split,
  strategist: Target,
  researcher_hub: Users,
  fact_checker: CheckCircle,
  synthesizer: FileText,
  reviewer: Eye,
};

export function ProcessState({ query, threadId, onComplete }: ProcessStateProps) {
  const [progress, setProgress] = useState(0);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [status, setStatus] = useState<"queued" | "running" | "completed" | "error">("queued");
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Poll for status updates
    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/research/status/${threadId}`);
        if (!response.ok) throw new Error("Failed to fetch status");

        const data = await response.json();
        setStatus(data.status);
        setProgress(data.progress_percentage || 0);
        setCurrentAgent(data.current_agent);

        if (data.status === "completed") {
          // Fetch final results
          const resultResponse = await fetch(`${API_BASE_URL}/api/research/result/${threadId}`);
          if (resultResponse.ok) {
            const result = await resultResponse.json();
            onComplete(result);
          }
        }
      } catch (error) {
        console.error("Error polling status:", error);
      }
    };

    // Set up SSE stream for real-time events
    const eventSource = new EventSource(`${API_BASE_URL}/api/research/stream/${threadId}`);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener("agent_update", (e) => {
      const event = JSON.parse(e.data);
      setEvents((prev) => [...prev, event]);
      setCurrentAgent(event.agent);
    });

    eventSource.addEventListener("status", (e) => {
      const data = JSON.parse(e.data);
      setStatus(data.status);
      setProgress(data.progress_percentage || 0);
    });

    eventSource.addEventListener("complete", (e) => {
      pollStatus(); // Fetch final results
    });

    eventSource.addEventListener("error", (e) => {
      console.error("SSE Error:", e);
      eventSource.close();
    });

    eventSource.addEventListener("done", () => {
      eventSource.close();
    });

    // Fallback polling every 2 seconds
    const pollInterval = setInterval(pollStatus, 2000);

    // Initial poll
    pollStatus();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      clearInterval(pollInterval);
    };
  }, [threadId, onComplete]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 -left-10 h-72 w-72 rounded-full bg-[#3182CE]/15 blur-3xl" />
        <div className="absolute inset-y-0 right-[-18%] h-[140%] w-1/2 rotate-6 bg-[linear-gradient(135deg,rgba(49,130,206,0.12),transparent_45%)] blur-3xl" />
        <div className="absolute bottom-[-30%] left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-white/5 blur-[110px]" />
      </div>

      <div className="relative z-10 px-4 py-12">
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="space-y-4 px-1">
            {/* Query Header */}
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-3">
                <Badge
                  variant="secondary"
                  className="rounded-full bg-[#3182CE] px-3 py-1 text-white shadow-lg shadow-[#3182CE]/25 hover:bg-[#2C5AA0]"
                >
                  Working
                </Badge>
                <span className="rounded-full bg-muted/60 px-3 py-1 text-xs text-muted-foreground">
                  Thread {threadId}
                </span>
              </div>
              <h2 className="text-2xl font-semibold text-foreground leading-tight">
                {query}
              </h2>
            </div>

            {/* Progress Bar */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-muted-foreground">Progress</span>
                <span className="rounded-full bg-[#3182CE]/15 px-3 py-1 font-semibold text-[#3182CE] shadow-inner shadow-[#3182CE]/20">
                  {progress}%
                </span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          </div>

          {/* Activity Feed */}
          <Card className="rounded-3xl border border-border/70 bg-card/80 p-6 shadow-2xl shadow-black/25 backdrop-blur">
            <div className="flex items-center gap-2 mb-6">
              <Loader2 className="h-5 w-5 animate-spin text-[#3182CE]" />
              <h3 className="text-lg font-semibold text-foreground">
                Live Activity
              </h3>
            </div>

            <div className="space-y-4">
              {events.length === 0 && (
                <div className="flex items-center gap-3 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin text-[#3182CE]" />
                  <span>Booting up the workflow…</span>
                </div>
              )}

              {events.map((event, idx) => {
                const Icon = AGENT_ICONS[event.agent] || Search;
                const isActive = event.agent === currentAgent;
                const isCompleted = idx < events.length - 1 || status === "completed";

                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-4 rounded-2xl border border-transparent bg-muted/30 p-4 transition-all ${
                      isActive
                        ? "border-[#3182CE]/60 shadow-lg shadow-[#3182CE]/10"
                        : "opacity-70"
                    }`}
                  >
                    <div className="flex-shrink-0 mt-1">
                      {isCompleted ? (
                        <CheckCircle2 className="h-6 w-6 text-green-500" />
                      ) : (
                        <Icon
                          className={`h-6 w-6 ${
                            isActive ? "text-[#3182CE] animate-pulse" : "text-muted-foreground"
                          }`}
                        />
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-foreground">
                          {event.agent_display_name}
                        </h4>
                        {isActive && (
                          <div className="flex gap-1">
                            <span className="h-2 w-2 bg-[#3182CE] rounded-full animate-pulse" />
                            <span className="h-2 w-2 bg-[#3182CE] rounded-full animate-pulse delay-75" />
                            <span className="h-2 w-2 bg-[#3182CE] rounded-full animate-pulse delay-150" />
                          </div>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {event.agent_description}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                );
              })}

              {status === "running" && currentAgent && (
                <div className="flex items-center gap-3 rounded-2xl border border-[#3182CE]/60 bg-muted/40 p-4 shadow-lg shadow-[#3182CE]/10">
                  <Loader2 className="h-5 w-5 animate-spin text-[#3182CE]" />
                  <span className="text-sm text-foreground">
                    Processing with {currentAgent}...
                  </span>
                </div>
              )}
            </div>
          </Card>

          {status === "error" && (
            <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-100">
              An error occurred during research. Please try again.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
