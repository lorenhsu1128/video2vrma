"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { VrmPreview } from "@/components/VrmPreview";
import {
  SharedTask,
  downloadBvhText,
  getSharedTask,
  overlayUrl,
  videoUrl,
} from "@/services/apiClient";
import { bvhTextToVrmaBlob } from "@/services/bvhToVrma";

export default function SharePage() {
  const params = useParams();
  const token = params.token as string;

  const [task, setTask] = useState<SharedTask | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [vrmaBlob, setVrmaBlob] = useState<Blob | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await getSharedTask(token);
        if (cancelled) return;
        setTask(data);
        if (data.has_bvh) {
          const bvh = await downloadBvhText(data.task_id);
          if (cancelled) return;
          const blob = await bvhTextToVrmaBlob(bvh, { scale: 0.01 });
          if (!cancelled) setVrmaBlob(blob);
        }
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    })();
    return () => { cancelled = true; };
  }, [token]);

  const onDownloadBvh = useCallback(async () => {
    if (!task) return;
    try {
      const bvh = await downloadBvhText(task.task_id);
      const blob = new Blob([bvh], { type: "application/octet-stream" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const stem = task.file_name.replace(/\.[^.]+$/, "");
      a.download = `${stem}.bvh`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(String(e));
    }
  }, [task]);

  const onDownloadVrma = useCallback(() => {
    if (!task || !vrmaBlob) return;
    const url = URL.createObjectURL(vrmaBlob);
    const a = document.createElement("a");
    a.href = url;
    const stem = task.file_name.replace(/\.[^.]+$/, "");
    a.download = `${stem}.vrma`;
    a.click();
    URL.revokeObjectURL(url);
  }, [task, vrmaBlob]);

  if (error) {
    return (
      <main style={mainStyle}>
        <h1>video2vrma — shared</h1>
        <pre style={{ color: "#c33", background: "#fee", padding: 12 }}>{error}</pre>
        <a href="/" style={{ color: "#39c" }}>back to home</a>
      </main>
    );
  }

  if (!task) {
    return (
      <main style={mainStyle}>
        <h1>video2vrma — shared</h1>
        <p>loading...</p>
      </main>
    );
  }

  return (
    <main style={mainStyle}>
      <h1 style={{ margin: 0 }}>video2vrma — shared</h1>
      <a href="/" style={{ color: "#39c", fontSize: "0.85em" }}>back to home</a>

      <table style={{ marginTop: 16, fontSize: "0.9em", borderCollapse: "collapse" }}>
        <tbody>
          <tr><td style={tdLabel}>file</td><td>{task.file_name}</td></tr>
          <tr><td style={tdLabel}>status</td><td>{task.status}</td></tr>
          <tr><td style={tdLabel}>created</td><td>{new Date(task.created_at).toLocaleString()}</td></tr>
          {task.tracks && (
            <tr><td style={tdLabel}>tracks</td><td>{task.tracks.length} ({task.total_frames} frames)</td></tr>
          )}
        </tbody>
      </table>

      <div style={{ display: "flex", gap: 10, marginTop: 16, flexWrap: "wrap" }}>
        {task.has_bvh && (
          <button onClick={onDownloadBvh} style={btnStyle}>download BVH</button>
        )}
        {vrmaBlob && (
          <button onClick={onDownloadVrma} style={btnStyle}>download VRMA</button>
        )}
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
        {task.has_video && (
          <div style={panelStyle}>
            <div style={labelStyle}>video</div>
            <video src={videoUrl(task.task_id)} controls muted playsInline style={mediaStyle} />
          </div>
        )}
        {task.has_overlay && (
          <div style={panelStyle}>
            <div style={labelStyle}>overlay</div>
            <video src={overlayUrl(task.task_id)} controls muted playsInline style={mediaStyle} />
          </div>
        )}
        {vrmaBlob && (
          <div style={panelStyle}>
            <div style={labelStyle}>VRM preview</div>
            <VrmPreview vrmUrl="/models/default.vrm" vrmaBlob={vrmaBlob} autoPlay />
          </div>
        )}
      </div>
    </main>
  );
}

const mainStyle: React.CSSProperties = {
  padding: "2rem",
  fontFamily: "sans-serif",
  maxWidth: 1200,
  margin: "0 auto",
};

const tdLabel: React.CSSProperties = {
  fontWeight: "bold",
  paddingRight: 16,
  color: "#666",
};

const btnStyle: React.CSSProperties = {
  padding: "6px 14px",
  background: "#3a6",
  color: "#fff",
  border: "none",
  borderRadius: 4,
  cursor: "pointer",
};

const panelStyle: React.CSSProperties = {
  flex: 1,
  minWidth: 200,
  border: "1px solid #444",
  borderRadius: 4,
  overflow: "hidden",
};

const labelStyle: React.CSSProperties = {
  padding: "4px 8px",
  background: "#333",
  color: "#fff",
  fontSize: "0.8em",
  textAlign: "center",
};

const mediaStyle: React.CSSProperties = {
  display: "block",
  width: "100%",
  height: "auto",
};
