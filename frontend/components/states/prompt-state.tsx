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
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-2xl">
        {/* Logo/Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-semibold text-foreground mb-2">
            Deep Research
          </h1>
        </div>

        {/* Main Input Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative">
            <Input
              type="text"
              placeholder="What deep topic shall we investigate today?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
              className="h-16 px-6 pr-16 text-lg shadow-lg bg-card border-border focus:border-[#3182CE] focus:ring-[#3182CE] rounded-2xl text-foreground placeholder:text-muted-foreground"
            />
            <Search className="absolute right-6 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          </div>

          <Button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="w-full h-14 text-lg font-medium bg-[#3182CE] hover:bg-[#2C5AA0] text-white rounded-2xl shadow-lg transition-all"
          >
            {isLoading ? "Starting Research..." : "Start Research"}
          </Button>
        </form>

        {/* Sub-text */}
        <p className="mt-8 text-center text-sm text-muted-foreground">
          Deep research may take several minutes. The agent will browse, read, and
          synthesize multiple sources.
        </p>

        {/* Example Queries */}
        <div className="mt-12">
          <p className="text-sm font-medium text-muted-foreground mb-4">
            Example queries:
          </p>
          <div className="space-y-2">
            {[
              "What are the latest developments in quantum computing?",
              "Compare and contrast renewable energy technologies",
              "Explain the economic impact of artificial intelligence",
            ].map((example, idx) => (
              <button
                key={idx}
                onClick={() => setQuery(example)}
                className="block w-full text-left px-4 py-3 text-sm text-foreground bg-card hover:bg-muted rounded-lg transition-colors border border-border"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
