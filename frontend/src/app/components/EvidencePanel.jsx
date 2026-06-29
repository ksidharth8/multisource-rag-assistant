import { formatNumber, sourceBadge } from "../lib/utils";

export default function EvidencePanel({ stats, sources, activity, copyText }) {
  return (
    <aside className="panel evidencePanel">
      <div className="panelHeader">
        <div>
          <h2>Evidence</h2>
          <p>Retrieved chunks and collection health.</p>
        </div>
      </div>

      <div className="statsGrid">
        <div className="statCard">
          <span>Documents</span>
          <strong>{formatNumber(stats?.documents)}</strong>
        </div>

        <div className="statCard">
          <span>Chunks</span>
          <strong>{formatNumber(stats?.chunks)}</strong>
        </div>

        <div className="statCard wide">
          <span>Characters</span>
          <strong>{formatNumber(stats?.characters)}</strong>
        </div>
      </div>

      <div className="sourceList">
        <div className="miniTitle">Retrieved sources</div>

        {sources.length === 0 ? (
          <div className="softEmpty">
            <div className="softEmptyIcon">⌕</div>
            <p>No retrieved chunks yet.</p>
            <small>After asking a question, matching chunks and similarity scores appear here.</small>
          </div>
        ) : (
          sources.map((source, index) => (
            <details key={`${source.metadata?.chunk_id || index}`} className="sourceCard" open={index === 0}>
              <summary>
                <span className="sourceBadge">{sourceBadge(source.source_type)}</span>
                <span className="sourceName">{source.source_name || "Unknown source"}</span>
                <span className="score">{source.score ?? "-"}</span>
              </summary>

              <div className="sourceToolbar">
                <span>Chunk {source.chunk_index ?? source.metadata?.chunk_index ?? "-"}</span>

                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    copyText(source.text, "Source chunk copied.");
                  }}
                >
                  Copy source
                </button>
              </div>

              <p>{source.text}</p>
            </details>
          ))
        )}
      </div>

      <div className="activity">
        <div className="miniTitle">Activity</div>

        {activity.length === 0 ? (
          <div className="softEmpty small">
            <p>No activity yet.</p>
          </div>
        ) : (
          activity.map((item) => (
            <div key={item.id} className="activityItem">
              <span>{item.time}</span>
              <p>{item.message}</p>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}