import { useMutation } from "@tanstack/react-query";

import { explore } from "@/lib/api/explore";

import type {
  ExploreRequest,
  ExploreResponse,
} from "@/types/explore";

export function useExplore() {
  return useMutation<ExploreResponse, Error, ExploreRequest>({
    mutationFn: explore,
  });
}
