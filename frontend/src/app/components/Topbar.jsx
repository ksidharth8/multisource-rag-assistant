import { classNames } from "../lib/utils";

export default function Topbar({ health, onRefresh }) {
  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">Production RAG Workspace</div>
        <h1>MultiSource RAG Assistant</h1>
        <p>Ingest sources, query with Groq, and inspect every retrieved chunk.</p>
      </div>

      <div className="topActions">
        <div className={classNames("statusPill", health)}>
          <span />
          {health === "online"
            ? "Backend online"
            : health === "offline"
            ? "Backend offline"
            : "Checking"}
        </div>

        <button className="ghostButton" onClick={onRefresh}>
          Refresh
        </button>
      </div>
    </header>
  );
}