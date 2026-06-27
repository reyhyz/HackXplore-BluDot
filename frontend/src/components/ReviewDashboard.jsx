import { useCallback, useEffect, useRef, useState } from "react";
import { deleteAllFiles, exportFiles, getFiles, uploadPDFs } from "../api/client.js";
import { STATUS } from "../types/index.js";
import ErrorDetailPage from "./ErrorDetailPage.jsx";
import { IconChevron, IconError, IconOk, IconSpinner, IconUpload, IconWarn } from "./Icons.jsx";
import StatusBadge from "./StatusBadge.jsx";

const FILTER_OPTIONS = ["All", "Error", "No Error", "Warning"];
const SORT_OPTIONS = [
  { label: "Default order",      value: "default" },
  { label: "Most issues first",  value: "most"    },
  { label: "Least issues first", value: "least"   },
];

export default function ReviewDashboard() {
  const [files, setFiles]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [uploading, setUploading]   = useState(false);
  const [selected, setSelected]     = useState(new Set());
  const [detailFile, setDetailFile] = useState(null);
  const [filter, setFilter]         = useState("All");
  const [sort, setSort]             = useState("default");
  const [filterOpen, setFilterOpen] = useState(false);
  const [dragOver, setDragOver]     = useState(false);
  const fileInputRef                = useRef(null);
  const dragCounterRef              = useRef(0); // track nested drag enter/leave

  // ── Fetch files on mount ─────────────────────────────────────────────────
  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFiles();
      setFiles(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Shared upload logic (used by both click and drop) ────────────────────
  const processFiles = useCallback(async (fileList) => {
    const pdfs = Array.from(fileList).filter((f) => f.type === "application/pdf");
    if (!pdfs.length) {
      setError("Only PDF files are accepted.");
      return;
    }
    try {
      setUploading(true);
      setError(null);
      await uploadPDFs(pdfs);
      await fetchFiles();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }, []);

  // ── Click upload ─────────────────────────────────────────────────────────
  const handleInputChange = (e) => {
    if (e.target.files?.length) processFiles(e.target.files);
    e.target.value = "";
  };

  // ── Drag and drop handlers ───────────────────────────────────────────────
  // Use a counter to handle nested drag events (e.g. dragging over child elements)
  const handleDragEnter = (e) => {
    e.preventDefault();
    dragCounterRef.current += 1;
    if (dragCounterRef.current === 1) setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    dragCounterRef.current -= 1;
    if (dragCounterRef.current === 0) setDragOver(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault(); // required to allow drop
  };

  const handleDrop = (e) => {
    e.preventDefault();
    dragCounterRef.current = 0;
    setDragOver(false);
    if (e.dataTransfer.files?.length) processFiles(e.dataTransfer.files);
  };

  // ── Remove all ───────────────────────────────────────────────────────────
  const handleRemoveAll = async () => {
    try {
      await deleteAllFiles();
      setFiles([]);
      setSelected(new Set());
    } catch (err) {
      setError(err.message);
    }
  };

  // ── Export handlers ──────────────────────────────────────────────────────
  const handleExport = async (mode) => {
    try {
      await exportFiles(mode, [...selected]);
    } catch (err) {
      setError(err.message);
    }
  };

  // ── Checkbox ─────────────────────────────────────────────────────────────
  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  // ── Filter + sort ────────────────────────────────────────────────────────
  const filtered = files
    .filter((f) => {
      if (filter === "Error")    return f.status === STATUS.ERROR;
      if (filter === "No Error") return f.status === STATUS.OK;
      if (filter === "Warning")  return f.status === STATUS.WARN;
      return true;
    })
    .sort((a, b) => {
      if (sort === "most")  return b.errors.length - a.errors.length;
      if (sort === "least") return a.errors.length - b.errors.length;
      return 0;
    });

  const errorCount = files.filter((f) => f.status === STATUS.ERROR).length;

  if (detailFile) {
    return <ErrorDetailPage file={detailFile} onBack={() => setDetailFile(null)} />;
  }

  return (
    <div
      className="min-h-screen bg-gray-100 text-gray-800 p-8 font-sans"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-gray-100 border-b border-gray-200">
        <div className="max-w-screen-xl mx-auto px-8 h-16 flex items-center justify-between">

          <div className="flex items-center gap-3">
            <div className="w-30 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              <img src="/logo-rentschler.png" alt="Logo" className="h-8 w-auto" />
            </div>
          </div>

        </div>
      </header>

      <div className="h-16 mb-4" />

      {/* Full-page drop overlay */}
      {dragOver && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center
          bg-blue-600/10 border-4 border-dashed border-blue-500 rounded-none pointer-events-none">
          <div className="bg-white rounded-2xl shadow-xl px-12 py-10 flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
              <IconUpload />
            </div>
            <p className="text-xl font-bold text-blue-700">Drop your PDFs here</p>
            <p className="text-sm text-gray-400">Only PDF files will be accepted</p>
          </div>
        </div>
      )}

      {/* Top bar */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Review Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Click on a file for detailed error reviews</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Upload button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50
              text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
          >
            {uploading ? <IconSpinner size={16} /> : <IconUpload />}
            {uploading ? "Processing…" : "Upload PDF"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            multiple
            className="hidden"
            onChange={handleInputChange}
          />

          {/* Error counter badge */}
          <div className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg px-5 py-3 shadow-sm">
            <span className="text-gray-500 text-sm font-medium">Files with Error</span>
            <span className="text-gray-900 text-4xl font-bold leading-none">{errorCount}</span>
            <span className="text-gray-400 text-sm">items</span>
            <IconError size={26} />
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-8 mb-7 text-sm text-gray-600">
        <div className="flex items-center gap-2"><IconWarn size={18} /><span>Unrecognized Handwriting</span></div>
        <div className="flex items-center gap-2"><IconError size={18} /><span>Error detected</span></div>
        <div className="flex items-center gap-2"><IconOk   size={18} /><span>No Error Detected</span></div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 ml-4 font-bold">✕</button>
        </div>
      )}

      {!loading && files.length === 0 && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="mb-6 border-2 border-dashed border-gray-300 hover:border-blue-400 rounded-xl
            py-14 flex flex-col items-center gap-3 cursor-pointer transition-colors group"
        >
          <div className="w-12 h-12 rounded-full bg-gray-100 group-hover:bg-blue-50 flex items-center justify-center transition-colors">
            <IconUpload />
          </div>
          <p className="text-gray-500 font-medium group-hover:text-blue-600 transition-colors">
            Drag & drop PDFs here, or click to browse
          </p>
          <p className="text-gray-400 text-xs">Supports multiple files at once</p>
        </div>
      )}

      {/* Table card */}
      {(loading || files.length > 0) && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden mb-6 shadow-sm">

          {/* Tab strip */}
          <div className="flex border-b border-gray-200">
            <div className="px-6 py-3 text-sm font-semibold text-blue-600 border-b-2 border-blue-600 -mb-px">
              Files
            </div>
          </div>

          {/* Filter / Sort row */}
          <div className="px-5 py-3 border-b border-gray-100 relative flex items-center gap-4 bg-gray-50">
            <button
              onClick={() => setFilterOpen((o) => !o)}
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 transition-colors font-medium"
            >
              Filter
              {filter !== "All" && (
                <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded text-xs font-medium">
                  {filter}
                </span>
              )}
              <IconChevron />
            </button>

            <div className="w-px h-4 bg-gray-300" />

            <div className="flex items-center gap-2">
              {SORT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSort(opt.value)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors border
                    ${sort === opt.value
                      ? "bg-blue-600 border-blue-600 text-white"
                      : "bg-white border-gray-300 text-gray-500 hover:text-gray-700 hover:border-gray-400"
                    }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {filterOpen && (
              <div className="absolute left-5 top-11 z-10 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[150px]">
                <p className="px-4 pt-2 pb-1 text-xs text-gray-400 uppercase tracking-wider font-semibold">Status</p>
                {FILTER_OPTIONS.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => { setFilter(opt); setFilterOpen(false); }}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors flex items-center justify-between
                      ${filter === opt ? "text-blue-600 font-medium" : "text-gray-700"}`}
                  >
                    {opt}
                    {filter === opt && (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <polyline points="2,6 5,9 10,3" stroke="#2563eb" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Table */}
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-400 text-xs uppercase tracking-wider border-b border-gray-200">
                <th className="text-left px-6 py-3 font-semibold">SAP Material Number</th>
                <th className="text-left px-6 py-3 font-semibold">Process Step</th>
                <th className="text-left px-6 py-3 font-semibold">Batch Number</th>
                <th className="text-left px-6 py-3 font-semibold">Issues</th>
                <th className="text-left px-6 py-3 font-semibold">Status</th>
                <th className="px-6 py-3 w-10" />
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-12">
                    <div className="flex items-center justify-center gap-2 text-gray-400">
                      <IconSpinner size={20} />
                      <span className="text-sm">Loading files…</span>
                    </div>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center text-gray-400 py-10 text-sm">
                    No files match this filter.
                  </td>
                </tr>
              ) : (
                filtered.map((file, idx) => (
                  <tr
                    key={file.id}
                    className={`border-b border-gray-100 hover:bg-blue-50/40 transition-colors
                      ${idx === filtered.length - 1 ? "border-b-0" : ""}`}
                  >
                    <td className="px-6 py-4 font-mono text-gray-600">{file.sapMaterial}</td>
                    <td className="px-6 py-4 text-gray-600">{file.processStep}</td>
                    <td className="px-6 py-4">
                      {file.errors.length > 0 ? (
                        <button
                          onClick={() => setDetailFile(file)}
                          className="text-blue-600 hover:text-blue-800 hover:underline transition-colors font-medium"
                        >
                          {file.batchNumber}
                        </button>
                      ) : (
                        <span className="text-blue-600 font-medium">{file.batchNumber}</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {file.errors.length > 0 ? (
                        <span className={`font-semibold ${file.status === STATUS.ERROR ? "text-red-500" : "text-yellow-500"}`}>
                          {file.errors.length}
                        </span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={file.status} />
                    </td>
                    <td className="px-6 py-4 text-center">
                      <input
                        type="checkbox"
                        checked={selected.has(file.id)}
                        onChange={() => toggleSelect(file.id)}
                        className="w-4 h-4 accent-blue-600 cursor-pointer"
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => handleExport("all")}
          className="px-6 py-3 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 transition-colors shadow-sm"
        >
          Export All
        </button>
        <button
          onClick={() => handleExport("no_error")}
          className="px-6 py-3 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 transition-colors shadow-sm flex items-center gap-2"
        >
          Export Only No Error <IconOk size={18} />
        </button>
        <button
          onClick={() => handleExport("selected")}
          disabled={selected.size === 0}
          className="px-6 py-3 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Export Selected {selected.size > 0 && `(${selected.size})`}
        </button>
        <button
          onClick={handleRemoveAll}
          className="px-6 py-3 bg-white hover:bg-gray-50 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 transition-colors shadow-sm"
        >
          Remove All
        </button>
      </div>
    </div>
  );
}
