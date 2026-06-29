import { classNames } from "../lib/utils";

export default function Toast({ toast }) {
  if (!toast) return null;

  return (
    <div className={classNames("toast", `toast-${toast.type}`)}>
      <span>{toast.type === "error" ? "!" : toast.type === "success" ? "✓" : "i"}</span>
      {toast.message}
    </div>
  );
}