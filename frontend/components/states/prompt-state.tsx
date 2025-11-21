"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PromptStateProps {
  onStartResearch: (query: string, threadId: string) => void;
}

export function PromptState({ onStartResearch }: PromptStateProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/research/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error("Failed to start research");
      }

      const data = await response.json();
      onStartResearch(query, data.thread_id);
    } catch (error) {
      console.error("Error starting research:", error);
      alert("Failed to start research. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-20 -left-10 h-72 w-72 rounded-full bg-[#3182CE]/15 blur-3xl" />
        <div className="absolute inset-y-0 right-[-18%] h-[140%] w-1/2 rotate-6 bg-[linear-gradient(135deg,rgba(49,130,206,0.12),transparent_45%)] blur-3xl" />
        <div className="absolute bottom-[-30%] left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-white/5 blur-[110px]" />
      </div>

      <div className="relative z-10 grid min-h-screen place-items-center px-4 py-12">
        <div className="w-full max-w-5xl space-y-8 translate-y-[-16%] md:translate-y-[-20%]">
          <div className="flex justify-center">
            <div className="flex items-center gap-2 rounded-full border border-border/70 bg-card/70 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground shadow-lg shadow-black/20 backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-[#3182CE] shadow-[0_0_0_6px_rgba(49,130,206,0.25)] animate-pulse" />
              Autonomous research pipeline
            </div>
          </div>

          <div className="space-y-4 text-center">
            <h1 className="text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
              Deep Research
            </h1>
          </div>

          <form onSubmit={handleSubmit} className="w-full">
            <div className="rounded-[28px] border border-border/70 bg-card/70 shadow-2xl shadow-black/25 backdrop-blur">
              <div className="flex flex-col gap-3 p-4 sm:p-6">
                <div className="relative flex items-center gap-3">
                  <Search className="h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="What are we diving deep into today?"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={isLoading}
                    className="h-14 flex-1 border-0 bg-transparent px-1 text-lg text-foreground placeholder:text-muted-foreground focus-visible:border-transparent focus-visible:ring-0 sm:h-16"
                  />
                  <div className="hidden h-10 w-px bg-border sm:block" />
                  <Button
                    type="submit"
                    disabled={!query.trim() || isLoading}
                    className="h-12 min-w-[160px] rounded-2xl border border-white/10 bg-[#3182CE] text-base font-semibold text-white shadow-lg shadow-[#3182CE]/25 transition-all hover:-translate-y-[1px] hover:bg-[#2C5AA0] focus-visible:ring-[#3182CE]/70 sm:h-14"
                  >
                    {isLoading ? "Starting…" : "Start Research"}
                  </Button>
                </div>
              </div>
            </div>
          </form>

        </div>
      </div>
    </div>
  );
}
