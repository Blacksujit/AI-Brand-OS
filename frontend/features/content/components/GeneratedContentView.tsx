"use client";

import { useState } from "react";
import { Copy, Edit2, Save, RotateCcw, Star, Calendar } from "lucide-react";
import { Button } from "@/features/ui/Button";
import { Input } from "@/features/ui/Input";
import { Textarea } from "@/features/ui/Textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/features/ui/Card";
import { Badge } from "@/features/ui/Badge";
import { QualityBadge } from "@/features/ui/QualityBadge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/features/ui/Dialog";
import { useRegenerateContent } from "@/features/content/hooks/useRegenerateContent";
import { useRateDraft } from "@/features/style/hooks/useStyleRate";
import { useUpdateRecordStatus } from "@/lib/api/hooks";
import { GeneratedPost } from "@/lib/validators/content";
import { toast } from "sonner";

interface GeneratedContentViewProps {
  post: GeneratedPost;
  onRegenerate: () => void;
}

export function GeneratedContentView({ post, onRegenerate }: GeneratedContentViewProps) {
  const [title, setTitle] = useState(post.title);
  const [hook, setHook] = useState(post.hook ?? "");
  const [body, setBody] = useState(post.body);
  const [cta, setCta] = useState(post.call_to_action ?? "");
  const [hashtags, setHashtags] = useState(post.hashtags?.join(" ") ?? "");
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [rateDialogOpen, setRateDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [scheduledAt, setScheduledAt] = useState("");

  const regenerate = useRegenerateContent();
  const rateDraft = useRateDraft();
  const updateStatus = useUpdateRecordStatus();

  const handleSave = async () => {
    setIsSaving(true);
    try {
      toast.success("Content saved to history");
      setIsEditing(false);
    } catch {
      toast.error("Failed to save");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerate = () => {
    regenerate.mutate(post.id);
    onRegenerate();
  };

  const handleRate = (rating: number) => {
    rateDraft.mutate({
      draft_id: post.id,
      score: rating,
      dimension_scores: { overall: rating },
    });
    setRateDialogOpen(false);
    toast.success(`Rated ${rating}/5 stars`);
  };

  const handleSchedule = async () => {
    if (!scheduledAt) {
      toast.error("Please select a date and time");
      return;
    }
    try {
      await updateStatus.mutateAsync({ recordId: post.id, status: "published" });
      toast.success(`Scheduled for ${new Date(scheduledAt).toLocaleString()}`);
      setScheduleDialogOpen(false);
    } catch {
      toast.error("Failed to schedule");
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const fullContent = [title, hook, body, cta, hashtags].filter(Boolean).join("\n\n");

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Generated Content</CardTitle>
          <div className="flex items-center gap-2">
            <QualityBadge score={post.quality_score ?? undefined} />
            <Badge variant="outline" className="text-xs capitalize">
              {post.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isEditing ? (
            <div className="space-y-4">
              <div>
                <p className="text-2xl font-bold">{title}</p>
                {hook && <p className="text-lg text-muted-foreground mt-2 italic">"{hook}"</p>}
              </div>
              <div className="prose prose-sm max-w-none">{body.split("\n").map((p) => <p key={p}>{p}</p>)}</div>
              {cta && <p className="font-medium text-primary">{cta}</p>}
              {hashtags && (
                <div className="flex flex-wrap gap-1">
                  {hashtags.split(" ").map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Title</label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Hook</label>
                <Input value={hook} onChange={(e) => setHook(e.target.value)} placeholder="Opening hook..." />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Body</label>
                <Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={8} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Call to Action</label>
                <Input value={cta} onChange={(e) => setCta(e.target.value)} placeholder="What should the reader do?" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Hashtags (space-separated)</label>
                <Input value={hashtags} onChange={(e) => setHashtags(e.target.value)} placeholder="#brandos #ai #content" />
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2 pt-4 border-t">
            {!isEditing ? (
              <>
                <Button variant="outline" onClick={() => setIsEditing(true)}>
                  <Edit2 className="mr-2 h-4 w-4" />
                  Edit
                </Button>
                <Button variant="outline" onClick={() => copyToClipboard(fullContent)}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy All
                </Button>
                <Button variant="secondary" onClick={handleRegenerate} disabled={regenerate.isPending}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  {regenerate.isPending ? "Regenerating..." : "Regenerate"}
                </Button>
                <Dialog open={rateDialogOpen} onOpenChange={setRateDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <Star className="mr-2 h-4 w-4" />
                      Rate Draft
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Rate this draft</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <Button
                          key={rating}
                          variant="outline"
                          className="w-full justify-start"
                          onClick={() => handleRate(rating)}
                        >
                          {rating} star{rating !== 1 ? "s" : ""}
                        </Button>
                      ))}
                    </div>
                  </DialogContent>
                </Dialog>
                <Dialog open={scheduleDialogOpen} onOpenChange={setScheduleDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline">
                      <Calendar className="mr-2 h-4 w-4" />
                      Schedule
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Schedule Post</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <Input
                        type="datetime-local"
                        value={scheduledAt}
                        onChange={(e) => setScheduledAt(e.target.value)}
                        min={new Date().toISOString().slice(0, 16)}
                      />
                      <DialogFooter>
                        <Button onClick={handleSchedule} disabled={!scheduledAt}>
                          Schedule
                        </Button>
                      </DialogFooter>
                    </div>
                  </DialogContent>
                </Dialog>
                <Button onClick={handleSave} disabled={isSaving} className="ml-auto">
                  <Save className="mr-2 h-4 w-4" />
                  {isSaving ? "Saving..." : "Save"}
                </Button>
              </>
            ) : (
              <>
                <Button onClick={handleSave} disabled={isSaving}>
                  <Save className="mr-2 h-4 w-4" />
                  {isSaving ? "Saving..." : "Save"}
                </Button>
                <Button variant="ghost" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}