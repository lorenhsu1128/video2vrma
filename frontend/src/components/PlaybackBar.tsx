"use client";

import { useCallback, useRef } from "react";

type Props = {
  duration: number;
  currentTime: number;
  onSeek?: (t: number) => void;
};

export function PlaybackBar({ duration, currentTime, onSeek }: Props) {
  const barRef = useRef<HTMLDivElement>(null);

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!onSeek || duration <= 0) return;
      const el = barRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      onSeek(ratio * duration);
    },
    [duration, onSeek],
  );

  const pct = duration > 0 ? Math.max(0, Math.min(1, currentTime / duration)) * 100 : 0;

  return (
    <div
      ref={barRef}
      onClick={handleClick}
      style={{
        position: "relative",
        height: 6,
        background: "#333",
        cursor: onSeek ? "pointer" : "default",
      }}
      title={duration > 0 ? `${currentTime.toFixed(1)} / ${duration.toFixed(1)}s` : undefined}
    >
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: `${pct}%`,
          background: "#3a6",
          transition: "width 0.08s linear",
        }}
      />
    </div>
  );
}
