"use client";

import { useState } from "react";
import { Button } from "@/features/ui/Button";
import { Textarea } from "@/features/ui/Textarea";
import { Input } from "@/features/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "@/features/ui/Card";
import { Badge } from "@/features/ui/Badge";
import { useEvaluateContent } from "@/lib/api/hooks";
import { EvaluateResponse } from "@/lib/validators/content";
import { Loader2, CheckCircle2, AlertCircle, Lightbulb, XCircle } from "lucide-react";

export function EvaluateForm() {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [platform, setPlatform] = useState("linkedin");

  const mutation = useEvaluateContent();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    mutation.mutate({ title, body, platform });
  };

  const data = mutation.data as EvaluateResponse | undefined;

  return (
    <Card className="space-y-4">
      <CardHeader>
        <CardTitle>Evaluate Content</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="evalTitle" className="text-sm font-medium">
              Title
            </label>
            <Input
              id="evalTitle"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter content title"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="evalBody" className="text-sm font-medium">
              Content Body
            </label>
            <Textarea
              id="evalBody"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Paste your content here..."
              rows={6}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="evalPlatform" className="text-sm font-medium">
              Platform
            </label>
            <select
              id="evalPlatform"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="linkedin">LinkedIn</option>
              <option value="twitter">Twitter / X</option>
              <option value="medium">Medium</option>
              <option value="newsletter">Newsletter</option>
            </select>
          </div>

          <Button type="submit" disabled={mutation.isPending || !title.trim() || !body.trim()}>
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Evaluating...
              </>
            ) : (
              "Evaluate Content"
            )}
          </Button>

          {mutation.isError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {mutation.error?.message || "Evaluation failed"}
            </div>
          )}
        </form>

        {data && (
          <div className="space-y-4 rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Evaluation Result</h3>
              <Badge variant={data.score >= 0.8 ? "success" : data.score >= 0.5 ? "warning" : "destructive"}>
                {Math.round(data.score * 100)}%
              </Badge>
            </div>

            <p className="font-medium">{data.verdict}</p>
            <p className="text-sm text-muted-foreground">{data.feedback}</p>

            {data.strengths.length > 0 && (
              <div className="space-y-1">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Lightbulb className="h-4 w-4" />
                  Strengths
                </h4>
                <ul className="space-y-1 text-sm">
                  {data.strengths.map((s, i) => (
                    <li key={i} className="flex items-center gap-2 text-green-600 dark:text-green-400">
                      <CheckCircle2 className="h-4 w-4" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {data.issues.length > 0 && (
              <div className="space-y-1">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  Issues
                </h4>
                <ul className="space-y-1 text-sm">
                  {data.issues.map((s, i) => (
                    <li key={i} className="flex items-center gap-2 text-destructive">
                      <XCircle className="h-4 w-4" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}