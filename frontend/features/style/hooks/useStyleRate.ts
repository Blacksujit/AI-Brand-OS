import { useMutation } from "@tanstack/react-query";
import { apiPost } from "@/lib/api/client";
import { RateDraftRequest } from "@/lib/validators/style";

export function useRateDraft() {
  return useMutation({
    mutationFn: (rating: RateDraftRequest) => apiPost("/style/rate", rating),
  });
}