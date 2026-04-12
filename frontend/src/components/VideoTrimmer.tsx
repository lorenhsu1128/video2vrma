"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type Props = {
  file: File;
  disabled?: boolean;
  onStart: (file: File, startTime: number, endTime: number) => void;
  onCancel: () => void;
};

function fmtTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec - m * 60;
  return `${m}:${s.toFixed(1).padStart(4, "0")}`;
}

export function VideoTrimmer({ file, disabled, onStart, onCancel }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [duration, setDuration] = useState(0);
  const [startTime, setStartTime] = useState(0);
  const [endTime, setEndTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const rafRef = useRef<number>(0);

  const objectUrl = useMemo(() => URL.createObjectURL(file), [file]);
  useEffect(() => () => URL.revokeObjectURL(objectUrl), [objectUrl]);

  const onLoaded = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    const dur = v.duration || 0;
    setDuration(dur);
    setStartTime(0);
    setEndTime(dur);
  }, []);

  useEffect(() => {
    const v = videoRef.current;
    if (!v || !playing) return;
    const check = () => {
      if (v.currentTime >= endTime) {
        v.pause();
        v.currentTime = startTime;
        setPlaying(false);
        return;
      }
      rafRef.current = requestAnimationFrame(check);
    };
    rafRef.current = requestAnimationFrame(check);
    return () => cancelAnimationFrame(rafRef.current);
  }, [playing, startTime, endTime]);

  const playSegment = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = startTime;
    v.play();
    setPlaying(true);
  }, [startTime]);

  const pause = useCallback(() => {
    videoRef.current?.pause();
    setPlaying(false);
  }, []);

  const onStartChange = useCallback(
    (val: number) => {
      const clamped = Math.min(val, endTime - 0.1);
      setStartTime(Math.max(0, clamped));
      const v = videoRef.current;
      if (v && !playing) v.currentTime = Math.max(0, clamped);
    },
    [endTime, playing],
  );

  const onEndChange = useCallback(
    (val: number) => {
      const clamped = Math.max(val, startTime + 0.1);
      setEndTime(Math.min(duration, clamped));
    },
    [startTime, duration],
  );

  const segmentDuration = Math.max(0, endTime - startTime);

  return (
    <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 16, marginTop: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <strong>影片預覽與時間段設定</strong>
        <span style={{ fontSize: "0.85em", color: "#666" }}>{file.name}</span>
      </div>

      <video
        ref={videoRef}
        src={objectUrl}
        onLoadedMetadata={onLoaded}
        onEnded={() => setPlaying(false)}
        style={{ width: "100%", maxHeight: 400, background: "#000", borderRadius: 4 }}
      />

      {duration > 0 && (
        <>
          <div style={{ marginTop: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <label style={{ minWidth: 70 }}>起始點：</label>
              <input
                type="range"
                min={0}
                max={duration}
                step={0.1}
                value={startTime}
                onChange={(e) => onStartChange(Number(e.target.value))}
                style={{ flex: 1 }}
              />
              <span style={{ minWidth: 50, textAlign: "right", fontFamily: "monospace" }}>
                {fmtTime(startTime)}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <label style={{ minWidth: 70 }}>結束點：</label>
              <input
                type="range"
                min={0}
                max={duration}
                step={0.1}
                value={endTime}
                onChange={(e) => onEndChange(Number(e.target.value))}
                style={{ flex: 1 }}
              />
              <span style={{ minWidth: 50, textAlign: "right", fontFamily: "monospace" }}>
                {fmtTime(endTime)}
              </span>
            </div>
            <div style={{ fontSize: "0.85em", color: "#666", marginBottom: 10 }}>
              片段長度：{fmtTime(segmentDuration)}（影片總長 {fmtTime(duration)}）
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button onClick={playing ? pause : playSegment} style={btnSecondary}>
              {playing ? "⏸ 暫停" : "▶ 預覽片段"}
            </button>
            <button
              onClick={() => onStart(file, startTime, endTime)}
              disabled={disabled || segmentDuration < 0.1}
              style={{
                ...btnPrimary,
                opacity: disabled || segmentDuration < 0.1 ? 0.5 : 1,
              }}
            >
              開始轉換
            </button>
            <button onClick={onCancel} disabled={disabled} style={btnSecondary}>
              取消
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const btnPrimary: React.CSSProperties = {
  padding: "8px 20px",
  background: "#2563eb",
  color: "#fff",
  border: "none",
  borderRadius: 4,
  cursor: "pointer",
  fontWeight: "bold",
};

const btnSecondary: React.CSSProperties = {
  padding: "8px 16px",
  background: "#eee",
  color: "#333",
  border: "1px solid #ccc",
  borderRadius: 4,
  cursor: "pointer",
};
