"use client";

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/features/ui/Card";
import { Badge } from "@/features/ui/Badge";
import { usePipelinePolling } from "@/lib/api/hooks";
import { CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/features/ui/Button";

const PIPELINE_STEPS = [
  { id: "research", label: "Researching Trends" },
  { id: "knowledge", label: "Retrieving Knowledge" },
  { id: "memory", label: "Loading Style Memory" },
  { id: "topic_selection", label: "Selecting Topic" },
  { id: "strategy", label: "Planning Strategy" },
  { id: "hook_generation", label: "Generating Hooks" },
  { id: "writing", label: "Writing Content" },
  { id: "review", label: "Quality Review" },
  { id: "analytics", label: "Finalizing" },
] as const;

type StepId = typeof PIPELINE_STEPS[number]["id"];

interface PipelineProgressProps {
  pipelineId: string;
  onComplete?: () => void;
}

export function PipelineProgress({ pipelineId, onComplete }: PipelineProgressProps) {
  const { data, isLoading, error, refetch } = usePipelinePolling(pipelineId);
  const completedRef = useRef(false);

  useEffect(() => {
    if (data?.is_complete && !completedRef.current) {
      completedRef.current = true;
      onComplete?.();
    }
  }, [data?.is_complete, onComplete]);

  const getStepStatus = (stepId: StepId): "pending" | "running" | "complete" | "error" => {
    if (!data) return "pending";

    const completedSteps = data.steps_completed || [];
    const errors = data.errors || [];

    if (errors.some((e) => e.step === stepId)) return "error";
    if (completedSteps.includes(stepId)) return "complete";
    if (data.current_step === stepId) return "running";
    return "pending";
  };

  const getStepDuration = (_stepId: StepId): number | undefined => {
    return undefined;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Pipeline Progress</span>
          <Badge variant={data?.is_complete ? "success" : data?.errors?.length ? "destructive" : "secondary"}>
            {data?.is_complete ? "Complete" : data?.errors?.length ? "Error" : "Running"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3" role="log" aria-live="polite" aria-label="Pipeline steps">
          {PIPELINE_STEPS.map((step, index) => {
            const status = getStepStatus(step.id);
            const isLast = index === PIPELINE_STEPS.length - 1;

            return (
              <div key={step.id} className="flex items-start gap-4">
                <div className="relative flex flex-col items-center">
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all",
                      status === "complete" && "bg-green-500 border-green-500 text-white",
                      status === "running" && "bg-primary border-primary text-primary-foreground animate-pulse",
                      status === "error" && "bg-red-500 border-red-500 text-white",
                      status === "pending" && "bg-muted border-muted-foreground/50 text-muted-foreground/50"
                    )}
                  >
                    {status === "complete" && <CheckCircle2 className="h-5 w-5" />}
                    {status === "running" && <Loader2 className="h-5 w-5 animate-spin" />}
                    {status === "error" && <AlertCircle className="h-5 w-5" />}
                    {status === "pending" && <span className="text-xs font-medium">{index + 1}</span>}
                  </div>
                  {!isLast && (
                    <div className="absolute left-4 top-8 bottom-8 w-0.5 bg-muted" />
                  )}
                </div>
                <div className="flex-1 min-w-0 pt-1">
                  <p className={cn("font-medium", status === "running" && "text-primary")}>
                    {step.label}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {status === "running" && (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin" />
                        <span>In progress...</span>
                      </>
                    )}
                    {status === "complete" && (
                      <>
                        <CheckCircle2 className="h-3 w-3 text-green-500" />
                        <span>Completed</span>
                      </>
                    )}
                    {status === "error" && (
                      <>
                        <AlertCircle className="h-3 w-3 text-red-500" />
                        <span>Error</span>
                      </>
                    )}
                    {status === "pending" && <span>Waiting...</span>}
                    {getStepDuration(step.id) && (
                      <span className="text-muted-foreground">
                        ({getStepDuration(step.id)}ms)
                      </span>
                    )}
                  </div>
                  {data?.errors?.some((e) => e.step === step.id) && (
                    <p className="mt-1 text-sm text-red-500">
                      {data.errors.find((e) => e.step === step.id)?.error}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {isLoading && (
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Polling for updates...</span>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-md border border-destructive/20 bg-destructive/5 p-3">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">Polling error</span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{error.message}</p>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-2">
              Retry
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}