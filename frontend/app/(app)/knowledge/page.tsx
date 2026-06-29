"use client";

import { useState } from "react";
import { Button } from "@/features/ui/Button";

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<unknown[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const { searchKnowledge } = await import("@/lib/api/knowledge");
      const data = await searchKnowledge(searchQuery);
      setResults(data.results || []);
    } catch {
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Knowledge Base</h1>
        <p className="text-muted-foreground">
          Search your ingested knowledge and reference materials.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search your knowledge base..."
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <Button type="submit" disabled={isSearching || !searchQuery.trim()}>
          {isSearching ? "Searching..." : "Search"}
        </Button>
      </form>

      {results.length === 0 && searchQuery && !isSearching && (
        <div className="flex items-center justify-center py-12">
          <p className="text-muted-foreground">No results found</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((entry: any) => (
            <div
              key={entry.id}
              className="rounded-lg border p-4 transition-colors hover:bg-muted/30"
            >
              <h3 className="font-medium">{entry.title}</h3>
              {entry.summary && (
                <p className="mt-1 text-sm text-muted-foreground">
                  {entry.summary}
                </p>
              )}
              <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                <span className="capitalize">{entry.source_type}</span>
                {entry.tags?.map((tag: string) => (
                  <span
                    key={tag}
                    className="rounded-full bg-secondary px-2 py-0.5 text-secondary-foreground"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
