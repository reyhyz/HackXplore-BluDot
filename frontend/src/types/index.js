/**
 * @typedef {"error" | "ok" | "warn"} FileStatus
 *
 * @typedef {Object} FileError
 * @property {string} field    - The field name where the error was detected
 * @property {string} value    - The extracted value that caused the error (or "—")
 * @property {string} message  - Human-readable explanation of the error
 *
 * @typedef {Object} ReviewFile
 * @property {string}      id          - Process step / file ID
 * @property {string}      sapMaterial - SAP Material Number
 * @property {string}      batchNumber - Batch number (7-digit numeric string)
 * @property {FileStatus}  status      - "error" | "ok" | "warn"
 * @property {FileError[]} errors      - List of detected issues (empty when status is "ok")
 */

export const STATUS = /** @type {const} */ ({
  ERROR: "error",
  OK:    "ok",
  WARN:  "warn",
});
