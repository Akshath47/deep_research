"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { FileDown, Copy, RotateCcw, CheckCircle2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ResearchResult } from "@/components/research-interface";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ResultStateProps {
  result: ResearchResult;
  onNewSearch: () => void;
}

export function ResultState({ result, onNewSearch }: ResultStateProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/research/pdf/${result.thread_id}`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error("PDF generation not yet implemented");
      }

      // TODO: Handle PDF download when implemented
      alert("PDF generation will be available soon!");
    } catch (error) {
      console.error("Error generating PDF:", error);
      alert("PDF generation is not yet available.");
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-24 -left-10 h-72 w-72 rounded-full bg-[#3182CE]/15 blur-3xl" />
        <div className="absolute inset-y-0 right-[-18%] h-[140%] w-1/2 rotate-6 bg-[linear-gradient(135deg,rgba(49,130,206,0.12),transparent_45%)] blur-3xl" />
        <div className="absolute bottom-[-30%] left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-white/5 blur-[110px]" />
      </div>

      <div className="relative z-10 px-4 py-12">
        <div className="max-w-5xl mx-auto space-y-8">
          {/* Action Bar */}
          <div className="sticky top-0 z-10 -mt-4 rounded-3xl border border-border/70 bg-card/70 px-6 py-4 shadow-2xl shadow-black/25 backdrop-blur">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-6 w-6 text-green-500" />
                <h2 className="text-2xl font-semibold text-foreground">
                  Research Complete
                </h2>
                <Badge variant="outline" className="rounded-full border-green-500/60 text-green-400">
                  Completed
                </Badge>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopy}
                  className="gap-2 rounded-xl border-border/70 bg-card/80"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadPDF}
                  className="gap-2 rounded-xl border-border/70 bg-card/80"
                >
                  <FileDown className="h-4 w-4" />
                  Download PDF
                </Button>

                <Button
                  size="sm"
                  onClick={onNewSearch}
                  className="gap-2 rounded-xl border border-white/10 bg-[#3182CE] text-white shadow-lg shadow-[#3182CE]/25 hover:bg-[#2C5AA0]"
                >
                  <RotateCcw className="h-4 w-4" />
                  New Search
                </Button>
              </div>
            </div>

            {/* Metadata */}
            <div className="flex items-center flex-wrap gap-3 mt-4 text-xs text-muted-foreground">
              <span className="rounded-full bg-muted/60 px-3 py-1">
                Thread {result.thread_id}
              </span>
              <span className="rounded-full bg-muted/60 px-3 py-1">
                Started {new Date(result.metadata.started_at).toLocaleString()}
              </span>
              <span className="rounded-full bg-muted/60 px-3 py-1">
                Completed {new Date(result.metadata.completed_at).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Main Report */}
          <Card className="rounded-3xl border border-border/70 bg-card/80 p-8 shadow-2xl shadow-black/25 backdrop-blur">
            <article className="prose prose-slate max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-3xl font-bold text-foreground mb-4 mt-6">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-2xl font-semibold text-foreground mb-3 mt-5">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-xl font-semibold text-foreground mb-2 mt-4">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-foreground leading-7 mb-4">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside text-foreground mb-4 space-y-2">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside text-foreground mb-4 space-y-2">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="ml-4">{children}</li>
                  ),
                  code: ({ children, className }) => {
                    const isInline = !className;
                    return isInline ? (
                      <code className="bg-muted text-[#3182CE] px-1.5 py-0.5 rounded text-sm">
                        {children}
                      </code>
                    ) : (
                      <code className="block bg-background text-foreground p-4 rounded-lg overflow-x-auto text-sm border border-border">
                        {children}
                      </code>
                    );
                  },
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-[#3182CE] pl-4 italic text-muted-foreground my-4">
                      {children}
                    </blockquote>
                  ),
                  a: ({ children, href }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#3182CE] hover:text-[#2C5AA0] underline"
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {result.report}
              </ReactMarkdown>
            </article>
          </Card>

          {/* Sub-Questions */}
          {result.subqueries && result.subqueries.length > 0 && (
            <Card className="rounded-3xl border border-border/70 bg-card/80 p-6 shadow-2xl shadow-black/25 backdrop-blur">
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Research Sub-Questions
              </h3>
              <ul className="space-y-2">
                {result.subqueries.map((subquery, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-muted-foreground"
                  >
                    <span className="text-[#3182CE] font-semibold">{idx + 1}.</span>
                    <span>{subquery}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Sources/Citations */}
          {result.citations && result.citations.length > 0 && (
            <Card className="rounded-3xl border border-border/70 bg-card/80 p-6 shadow-2xl shadow-black/25 backdrop-blur">
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="sources">
                  <AccordionTrigger className="text-lg font-semibold text-foreground">
                    Sources Used ({result.citations.length})
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-4 mt-4">
                      {result.citations.map((citation, idx) => (
                        <div
                          key={idx}
                          className="p-4 bg-muted/40 rounded-2xl border border-border/70"
                        >
                          <p className="text-sm font-medium text-[#3182CE] mb-2">
                            {citation.file}
                          </p>
                          <div className="text-sm text-muted-foreground max-h-40 overflow-y-auto">
                            <ReactMarkdown>{citation.content}</ReactMarkdown>
                          </div>
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
