import { STATUS } from "../types/index.js";
import { IconError, IconOk, IconWarn } from "./Icons.jsx";

export default function StatusBadge({ status }) {
  if (status === STATUS.ERROR) return <IconError />;
  if (status === STATUS.OK)    return <IconOk />;
  return <IconWarn />;
}
