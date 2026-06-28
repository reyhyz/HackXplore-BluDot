import { useCallback, useEffect, useState } from "react";
import { STATUS } from "../types/index.js";
import { IconBack, IconError, IconWarn } from "./Icons.jsx";
import StatusBadge from "./StatusBadge.jsx";

const storageKey = (fileId, idx) => `resolved:${fileId}:${idx}`;

function loadResolved(fileId, errorCount) {
  const resolved = new Set();
  for (let i = 0; i < errorCount; i++) {
    if (localStorage.getItem(storageKey(fileId, i)) === "1") resolved.add(i);
  }
  return resolved;
}

function saveResolved(fileId, idx, value) {
  if (value) {
    localStorage.setItem(storageKey(fileId, idx), "1");
  } else {
    localStorage.removeItem(storageKey(fileId, idx));
  }
}

/**
 * @param {{ file: import("../types/index.js").ReviewFile, onBack: () => void }} props
 */
export default function ErrorDetailPage({ file, onBack }) {
  const [resolved, setResolved] = useState(() =>
    loadResolved(file.id, file.errors.length)
  );
  const [copyFeedback, setCopyFeedback] = useState(false);

  useEffect(() => {
    setResolved(loadResolved(file.id, file.errors.length));
  }, [file.id, file.errors.length]);

  const toggleResolved = useCallback(
    (idx) => {
      setResolved((prev) => {
        const next = new Set(prev);
        if (next.has(idx)) {
          next.delete(idx);
          saveResolved(file.id, idx, false);
        } else {
          next.add(idx);
          saveResolved(file.id, idx, true);
        }
        return next;
      });
    },
    [file.id]
  );

  const resolvedCount = resolved.size;
  const totalCount    = file.errors.length;
  const allDone       = resolvedCount === totalCount && totalCount > 0;
  const progress      = totalCount > 0 ? (resolvedCount / totalCount) * 100 : 0;

  const handleCopySummary = () => {
    const lines = [
      `Batch: ${file.batchNumber}`,
      `SAP Material: ${file.sapMaterial}`,
      `Process Step: ${file.processStep}`,
      `Resolved: ${resolvedCount} / ${totalCount}`,
      "",
      ...file.errors.map((err, i) => {
        const status   = resolved.has(i) ? "[RESOLVED]" : "[OPEN]";
        const severity = err.severity === "warn" ? "[UNCLEAR]" : "[ERROR]";
        const parts    = [`${status} ${severity} ${err.field}`];
        if (err.value && err.value !== "—") parts.push(`  Value: ${err.value}`);
        parts.push(`  Note: ${err.message}`);
        return parts.join("\n");
      }),
    ];
    navigator.clipboard.writeText(lines.join("\n")).then(() => {
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 2000);
    });
  };

  return (
    <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-4xl">
        <button
          onClick={onBack}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-900"
        >
          <IconBack />
          <span>Back to dashboard</span>
        </button>

        <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/90 shadow-[0_20px_60px_-30px_rgba(15,23,42,0.35)] backdrop-blur">

          {/* Header */}
          <div className="border-b border-slate-200 bg-gradient-to-r from-slate-50 to-[#2F70B3]/10 px-6 py-6 sm:px-8">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Error review</p>
            <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                  Batch number {file.batchNumber}
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                  Review the captured metadata and the detected issues below.
                </p>
              </div>
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Issues</span>
                <span className="text-3xl font-semibold text-slate-900">{totalCount}</span>
              </div>
            </div>
          </div>

          <div className="space-y-6 px-6 py-6 sm:px-8">

            {/* Meta card */}
            <div className="grid gap-4 rounded-[1.5rem] border border-slate-200 bg-slate-50/80 p-5 sm:grid-cols-2">
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">SAP Material Number</p>
                <p className="font-mono text-sm text-slate-900">{file.sapMaterial}</p>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Process Step</p>
                <p className="font-mono text-sm text-slate-900">{file.processStep}</p>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Status</p>
                <div className="flex items-center gap-3">
                  <StatusBadge status={file.status} />
                  <span className="text-sm font-medium text-slate-700">
                    {file.status === STATUS.ERROR
                      ? "Error detected"
                      : file.status === STATUS.WARN
                      ? "Unrecognized handwriting"
                      : "No errors"}
                  </span>
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Issues found</p>
                <p className="text-sm font-semibold text-rose-600">{totalCount}</p>
              </div>
            </div>

            {/* Resolution progress */}
            <div className={`rounded-[1.5rem] border p-5 transition-colors ${allDone ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-slate-50/80"}`}>
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Resolution progress</p>
                  <p className="mt-1 text-sm font-medium text-slate-700">
                    {resolvedCount} of {totalCount} issue{totalCount !== 1 ? "s" : ""} resolved
                    {allDone && (
                      <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                        ✓ All done
                      </span>
                    )}
                  </p>
                </div>
                <button
                  onClick={handleCopySummary}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-900 active:scale-95"
                >
                  {copyFeedback ? (
                    <><svg width="12" height="12" viewBox="0 0 12 12" fill="none"><polyline points="2,6 5,9 10,3" stroke="#059669" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg><span className="text-emerald-600">Copied!</span></>
                  ) : (
                    <><svg width="12" height="12" viewBox="0 0 12 12" fill="none"><rect x="4" y="1" width="7" height="8" rx="1" stroke="currentColor" strokeWidth="1.4" /><rect x="1" y="3" width="7" height="8" rx="1" stroke="currentColor" strokeWidth="1.4" fill="white" /></svg>Copy summary</>
                  )}
                </button>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${allDone ? "bg-emerald-500" : "bg-[#2F70B3]"}`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Error list */}
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">Detected issues</h2>
              <div className="mt-4 space-y-3">
                {file.errors.map((err, i) => {
                  const isResolved = resolved.has(i);
                  // "warn" severity → unclear/handwriting → yellow icon
                  // "error" severity → hard error → red icon
                  const isWarn = err.severity === "warn";

                  return (
                    <div
                      key={i}
                      className={`flex gap-4 rounded-[1.25rem] border p-5 shadow-sm transition-colors ${
                        isResolved
                          ? "border-emerald-100 bg-emerald-50/60"
                          : isWarn
                          ? "border-amber-100 bg-amber-50/40"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      {/* Icon */}
                      <div className="shrink-0 pt-0.5">
                        {isResolved ? (
                          <span className="flex h-[18px] w-[18px] items-center justify-center rounded-full bg-emerald-500">
                            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                              <polyline points="1.5,5 4,7.5 8.5,2.5" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          </span>
                        ) : isWarn ? (
                          <IconWarn size={18} />   // yellow — unrecognized handwriting / unclear
                        ) : (
                          <IconError size={18} />  // red — hard error
                        )}
                      </div>

                      {/* Content */}
                      <div className="min-w-0 flex-1 text-sm">
                        <p className={`mb-1 text-xs font-semibold uppercase tracking-[0.18em] transition-colors ${
                          isResolved ? "text-emerald-500" : isWarn ? "text-amber-500" : "text-slate-400"
                        }`}>
                          {err.field}
                          {isResolved && <span className="ml-2 normal-case tracking-normal font-medium text-emerald-500">· Resolved</span>}
                          {!isResolved && isWarn && <span className="ml-2 normal-case tracking-normal font-medium text-amber-500">· Unclear</span>}
                        </p>
                        {err.value !== "—" && (
                          <p className={`mb-1 font-mono transition-colors ${isResolved ? "text-slate-400 line-through" : "text-slate-700"}`}>
                            {err.value}
                          </p>
                        )}
                        <p className={`leading-6 transition-colors ${isResolved ? "text-slate-400" : "text-slate-500"}`}>
                          {err.message}
                        </p>
                      </div>

                      {/* Resolve toggle */}
                      <div className="shrink-0 self-center">
                        <button
                          onClick={() => toggleResolved(i)}
                          className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all active:scale-95 ${
                            isResolved
                              ? "border-emerald-200 bg-white text-emerald-600 hover:bg-emerald-50 hover:border-emerald-300"
                              : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900"
                          }`}
                        >
                          {isResolved ? "Undo" : "Mark resolved"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}