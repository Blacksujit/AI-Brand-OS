"use client";

import { useState } from "react";
import { Search, X } from "lucide-react";
import { useKnowledgeList, useKnowledgeTags } from "@/features/knowledge/hooks/useKnowledge";
import { KnowledgeCard } from "@/features/knowledge/components/KnowledgeCard";
import { AddKnowledgeModal } from "@/features/knowledge/components/AddKnowledgeModal";
import { Button } from "@/features/ui/Button";
import { Input } from "@/features/ui/Input";
import { Badge } from "@/features/ui/Badge";
import { toast } from "sonner";

export default function KnowledgePage() {
  const [page, setPage] = useState(1);
  const [selectedTag, setSelectedTag] = useState<string | undefined>();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data, isLoading, isError, error } = useKnowledgeList({
    page,
    page_size: 20,
    tag: selectedTag,
  });
  const { data: tagsData } = useKnowledgeTags();

  const items = data?.items ?? [];
  const tags = tagsData ?? [];
  const totalCount = data?.total_count ?? 0;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(searchInput.trim());
    setPage(1);
    setSelectedTag(undefined);
  };

  const handleTagClick = (tag: string) => {
    setSelectedTag(selectedTag === tag ? undefined : tag);
    setPage(1);
    setSearchQuery("");
    setSearchInput("");
  };

  const handleDelete = async (id: string) => {
    try {
      const { deleteKnowledgeEntry } = await import("@/lib/api/knowledge");
      await deleteKnowledgeEntry(id);
      toast.success("Entry deleted");
      // Refetch happens via hook invalidation — use a simple reload
      setPage(1);
    } catch {
      toast.error("Failed to delete entry");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-muted-foreground">
            Your ingested knowledge and reference materials.
          </p>
        </div>
        <AddKnowledgeModal />
      </div>

      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search your knowledge base..."
            className="pl-9"
          />
        </div>
        <Button type="submit" disabled={!searchInput.trim()}>
          Search
        </Button>
        {searchQuery && (
          <Button
            variant="ghost"
            onClick={() => {
              setSearchQuery("");
              setSearchInput("");
            }}
          >
            <X className="mr-2 h-4 w-4" />
            Clear
          </Button>
        )}
      </form>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <span className="text-xs text-muted-foreground self-center mr-1">
            Tags:
          </span>
          {tags.map((tag) => (
            <Badge
              key={tag.name}
              variant={selectedTag === tag.name ? "default" : "secondary"}
              className="cursor-pointer text-xs"
              onClick={() => handleTagClick(tag.name)}
            >
              {tag.name} ({tag.count})
            </Badge>
          ))}
          {selectedTag && (
            <Button
              variant="ghost"
              size="sm"
              className="h-5 text-xs"
              onClick={() => setSelectedTag(undefined)}
            >
              <X className="mr-1 h-3 w-3" />
              Clear
            </Button>
          )}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      )}

      {isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {error?.message || "Failed to load knowledge base"}
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-muted-foreground">No entries yet</p>
            <p className="text-sm text-muted-foreground">
              {searchQuery
                ? "No results match your search."
                : "Add your first knowledge entry to get started."}
            </p>
          </div>
        </div>
      )}

      {items.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((entry) => (
            <KnowledgeCard
              key={entry.id}
              id={entry.id}
              title={entry.title}
              summary={entry.summary}
              source_type={entry.source_type}
              tags={entry.tags}
              created_at={entry.created_at}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {totalCount > page * 20 && (
        <div className="flex justify-center pt-4">
          <Button variant="outline" onClick={() => setPage((p) => p + 1)}>
            Load More
          </Button>
        </div>
      )}
    </div>
  );
}
