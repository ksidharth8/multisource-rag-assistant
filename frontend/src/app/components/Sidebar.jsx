import { SOURCE_TABS } from "../lib/constants";
import { classNames } from "../lib/utils";

export default function Sidebar({
  collectionName,
  setCollectionName,
  collections,
  activeTab,
  setActiveTab,
  sourceName,
  setSourceName,
  rawText,
  setRawText,
  url,
  setUrl,
  youtubeUrl,
  setYoutubeUrl,
  file,
  setFile,
  ingestLoading,
  handleIngest,
  handleDeleteCollection,
}) {
  const activeTabMeta = SOURCE_TABS.find((tab) => tab.id === activeTab);

  function renderIngestInput() {
    if (activeTab === "text") {
      return (
        <textarea
          className="input textarea"
          placeholder="Paste notes, documentation, transcript, or any raw text here..."
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
      );
    }

    if (activeTab === "file") {
      return (
        <label className="dropzone">
          <input
            type="file"
            accept=".pdf,.txt,.md,.docx,.pptx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <span className="dropIcon">↥</span>
          <strong>{file ? file.name : "Choose document"}</strong>
          <small>PDF, TXT, MD, DOCX, PPTX</small>
        </label>
      );
    }

    if (activeTab === "url") {
      return (
        <input
          className="input"
          placeholder="https://example.com/article"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      );
    }

    return (
      <input
        className="input"
        placeholder="https://www.youtube.com/watch?v=..."
        value={youtubeUrl}
        onChange={(e) => setYoutubeUrl(e.target.value)}
      />
    );
  }

  return (
    <aside className="panel sidebar">
      <div className="panelHeader">
        <div>
          <h2>Workspace</h2>
          <p>Choose a knowledge collection.</p>
        </div>
      </div>

      <label className="field">
        <span>Collection name</span>
        <input
          className="input"
          value={collectionName}
          onChange={(e) => setCollectionName(e.target.value)}
          placeholder="e.g. dsa-placement-master"
        />
      </label>

      <div className="quickCollections">
        <div className="miniTitle">Recent collections</div>

        {collections.length === 0 ? (
          <div className="softEmpty small">
            <p>No collections found yet.</p>
          </div>
        ) : (
          <div className="collectionList">
            {collections.slice(0, 7).map((item) => (
              <button
                key={item}
                className={classNames("collectionChip", item === collectionName && "active")}
                onClick={() => setCollectionName(item)}
              >
                {item}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="divider" />

      <div className="panelHeader compact">
        <div>
          <h2>Add source</h2>
          <p>{activeTabMeta?.hint}</p>
        </div>
      </div>

      <div className="tabs">
        {SOURCE_TABS.map((tab) => (
          <button
            key={tab.id}
            className={classNames("tab", activeTab === tab.id && "active")}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {(activeTab === "text" || activeTab === "file") && (
        <label className="field">
          <span>Source name</span>
          <input
            className="input"
            value={sourceName}
            onChange={(e) => setSourceName(e.target.value)}
            placeholder={activeTab === "file" ? "Defaults to filename" : "e.g. lecture_1"}
          />
        </label>
      )}

      {renderIngestInput()}

      <button className="primaryButton" onClick={handleIngest} disabled={ingestLoading}>
        {ingestLoading ? "Ingesting..." : "Ingest source"}
      </button>

      <button className="dangerButton" onClick={handleDeleteCollection}>
        Delete collection
      </button>
    </aside>
  );
}