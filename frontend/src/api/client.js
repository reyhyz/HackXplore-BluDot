/**
 * api/client.js
 * Talks to the FastAPI backend (main.py).
 * 
 */

const BASE = "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res;
}

/** GET /files — returns the current list of processed FileRecords */
export async function getFiles() {
  const res = await request("/files");
  return res.json();
}

/**
 * POST /upload — send one or more PDF File objects.
 * Returns the newly created FileRecords so the dashboard can append them.
 */
export async function uploadPDFs(files) {
  const form = new FormData();
  for (const file of files) form.append("files", file);

  const res = await request("/upload", { method: "POST", body: form });
  return res.json();
}

/** DELETE /files — wipe the in-memory store */
export async function deleteAllFiles() {
  await request("/files", { method: "DELETE" });
}

/**
 * POST /export — triggers Excel generation on the server and downloads the file.
 *
 * @param {"all"|"no_error"|"selected"} mode
 * @param {string[]} fileIds  — only used when mode === "selected"
 */
export async function exportFiles(mode, fileIds = []) {
  const res = await request("/export", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ mode, file_ids: fileIds }),
  });

  // Stream the .xlsx blob and prompt the browser's Save-As dialog
  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");

  // Use the filename the server suggested, or fall back to a default
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match       = disposition.match(/filename=([^;]+)/);
  a.download = match ? match[1] : `batch_review_${mode}.xlsx`;

  a.href = url;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}