import { useReducedMotion } from "framer-motion";

export type Direction = "up" | "left" | "right" | "none";

export function useEntrance(direction: Direction = "up") {
  const reduce = useReducedMotion();

  if (reduce || direction === "none") {
    return { initial: undefined, whileInView: undefined, viewport: { once: true } as const };
  }

  const offsets: Record<Exclude<Direction, "none">, { opacity: 0; y?: number; x?: number }> = {
    up: { opacity: 0, y: 24 },
    left: { opacity: 0, x: -24 },
    right: { opacity: 0, x: 24 },
  };

  const resets: Record<Exclude<Direction, "none">, { y?: number; x?: number }> = {
    up: { y: 0 },
    left: { x: 0 },
    right: { x: 0 },
  };

  return {
    initial: offsets[direction],
    whileInView: { opacity: 1, ...resets[direction] },
    viewport: { once: true } as const,
  };
}

export function useItemAnimation(index: number = 0, baseDelay: number = 0.1) {
  const reduce = useReducedMotion();
  return reduce ? {} : { transition: { duration: 0.5, delay: index * baseDelay } };
}
