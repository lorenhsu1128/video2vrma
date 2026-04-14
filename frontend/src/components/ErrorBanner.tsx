"use client";

import { useEffect } from "react";

export type ErrorBannerVariant = "error" | "info";

type Props = {
  message: string;
  variant?: ErrorBannerVariant;
  onDismiss: () => void;
  autoHideMs?: number;
};

const PALETTE: Record<ErrorBannerVariant, { fg: string; bg: string; border: string }> = {
  error: { fg: "#8a1f1f", bg: "#fee", border: "#e9b4b4" },
  info: { fg: "#1f5f3a", bg: "#e6f7ec", border: "#a8d8ba" },
};

export function ErrorBanner({ message, variant = "error", onDismiss, autoHideMs }: Props) {
  useEffect(() => {
    if (!autoHideMs) return;
    const id = setTimeout(onDismiss, autoHideMs);
    return () => clearTimeout(id);
  }, [autoHideMs, onDismiss]);

  const c = PALETTE[variant];

  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        padding: "10px 12px",
        background: c.bg,
        border: `1px solid ${c.border}`,
        borderRadius: 4,
        color: c.fg,
        marginBottom: 12,
        fontSize: "0.9em",
      }}
    >
      <div style={{ flex: 1, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{message}</div>
      <button
        onClick={onDismiss}
        aria-label="dismiss"
        style={{
          background: "transparent",
          border: "none",
          color: c.fg,
          cursor: "pointer",
          fontSize: "1.1em",
          lineHeight: 1,
          padding: "0 2px",
        }}
      >
        ×
      </button>
    </div>
  );
}
