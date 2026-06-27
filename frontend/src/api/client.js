const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}/api${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? "Request failed");
  }
  return res.json();
}

// ── Files ─────────────────────────────────────────────────────────────────────

/** GET /api/files — fetch all processed files */
export const getFiles = () => request("/files");

/** DELETE /api/files — remove all files */
export const deleteAllFiles = () => request("/files", { method: "DELETE" });

/** DELETE /api/files/{id} — remove a single file */
export const deleteFile = (id) => request(`/files/${id}`, { method: "DELETE" });

// ── Upload ────────────────────────────────────────────────────────────────────

/**
 * POST /api/upload — upload one or more PDFs for digitisation.
 * @param {File[]} files - array of File objects from an <input type="file">
 */
export const uploadPDFs = (files) => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return fetch(`${BASE_URL}/api/upload`, { method: "POST", body: form }).then((r) => {
    if (!r.ok) throw new Error("Upload failed");
    return r.json();
  });
};

// ── Export ────────────────────────────────────────────────────────────────────

/**
 * GET /api/export?ids=...&filter=... — download an Excel file from the backend.
 * Falls back to a client-side CSV if you haven't wired up the endpoint yet.
 * @param {"all"|"no_error"|"selected"} mode
 * @param {string[]} [ids] - required when mode === "selected"
 */
export const exportFiles = async (mode, ids = []) => {
  const params = new URLSearchParams({ mode });
  if (mode === "selected") ids.forEach((id) => params.append("ids", id));

  const res = await fetch(`${BASE_URL}/api/export?${params}`);
  if (!res.ok) throw new Error("Export failed");

  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `export_${mode}.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
};
