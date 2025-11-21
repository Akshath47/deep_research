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
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Query Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-2xl font-semibold text-foreground">
              {query}
            </h2>
            <Badge
              variant="secondary"
              className="bg-[#3182CE] text-white hover:bg-[#2C5AA0]"
            >
              Researching...
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Thread ID: {threadId}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-muted-foreground">
              Overall Progress
            </span>
            <span className="text-sm font-medium text-[#3182CE]">
              {progress}%
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Activity Feed */}
        <Card className="p-6 bg-card shadow-lg border-border">
          <h3 className="text-lg font-semibold text-foreground mb-6">
            Live Activity Feed
          </h3>

          <div className="space-y-4">
            {events.length === 0 && (
              <div className="flex items-center gap-3 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin text-[#3182CE]" />
                <span>Initializing research...</span>
              </div>
            )}

            {events.map((event, idx) => {
              const Icon = AGENT_ICONS[event.agent] || Search;
              const isActive = event.agent === currentAgent;
              const isCompleted = idx < events.length - 1 || status === "completed";

              return (
                <div
                  key={idx}
                  className={`flex items-start gap-4 p-4 rounded-lg transition-all ${
                    isActive
                      ? "bg-muted border-l-4 border-[#3182CE]"
                      : "opacity-60"
                  }`}
                >
                  <div className="flex-shrink-0 mt-1">
                    {isCompleted ? (
                      <CheckCircle2 className="h-6 w-6 text-green-600" />
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

            {/* Current Agent Indicator */}
            {status === "running" && currentAgent && (
              <div className="flex items-center gap-3 p-4 bg-muted rounded-lg border-l-4 border-[#3182CE]">
                <Loader2 className="h-5 w-5 animate-spin text-[#3182CE]" />
                <span className="text-sm text-foreground">
                  Processing with {currentAgent}...
                </span>
              </div>
            )}
          </div>
        </Card>

        {/* Status Messages */}
        {status === "error" && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">
              An error occurred during research. Please try again.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
