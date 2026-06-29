import { EXAMPLE_QUESTIONS, PERSONAS } from "../lib/constants";
import AnswerBlocks from "./AnswerBlocks";

export default function ChatPanel({
  question,
  setQuestion,
  persona,
  setPersona,
  topK,
  setTopK,
  answer,
  sources,
  queryLoading,
  handleAsk,
  handleClearQuestion,
  handleClearMemory,
  chatHistory,
  copyText,
  answerRef,
}) {
  const memoryTurns = Math.floor((chatHistory?.length || 0) / 2);

  return (
    <section className="panel chatPanel">
      <div className="panelHeader">
        <div>
          <h2>Ask grounded questions</h2>
          <p>Answers are generated only after retrieving relevant chunks.</p>
          <p className="muted">
            Memory: {memoryTurns} turn{memoryTurns === 1 ? "" : "s"} stored locally.
          </p>
        </div>

        <div className="queryControls">
          <select value={persona} onChange={(e) => setPersona(e.target.value)} className="select">
            {PERSONAS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>

          <select value={topK} onChange={(e) => setTopK(e.target.value)} className="select">
            {[1, 2, 3, 4, 5, 8].map((n) => (
              <option key={n} value={n}>
                Top {n}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="questionBox">
        <textarea
          className="questionInput"
          placeholder="Ask something from your uploaded sources..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") handleAsk();
          }}
        />

        <div className="questionFooter">
          <span>Press Cmd/Ctrl + Enter to ask</span>

          <div className="questionActions">
            <button className="secondaryButton" onClick={handleClearQuestion} disabled={!question && !answer}>
              Clear
            </button>

            <button className="secondaryButton" onClick={handleClearMemory} disabled={!chatHistory?.length}>
              Clear memory
            </button>

            <button className="askButton" onClick={handleAsk} disabled={queryLoading}>
              {queryLoading ? "Thinking..." : "Ask"}
            </button>
          </div>
        </div>
      </div>

      {!answer && !queryLoading && (
        <div className="promptSuggestions">
          <div className="miniTitle">Try asking</div>

          <div className="suggestionGrid">
            {EXAMPLE_QUESTIONS.map((item) => (
              <button key={item} className="suggestionCard" onClick={() => setQuestion(item)}>
                {item}
              </button>
            ))}
          </div>
        </div>
      )}

      <div ref={answerRef} className="answerArea">
        {!answer && !queryLoading && (
          <div className="emptyState improved">
            <div className="emptyOrb">R</div>
            <h3>No answer yet</h3>
            <p>
              Select a collection, ingest at least one source, then ask a question. The answer will
              appear here with retrieved evidence on the right.
            </p>

            <div className="emptyChecklist">
              <span>1. Add source</span>
              <span>2. Ask question</span>
              <span>3. Verify evidence</span>
            </div>
          </div>
        )}

        {queryLoading && (
          <div className="loadingAnswer">
            <div className="skeleton title" />
            <div className="skeleton line" />
            <div className="skeleton line short" />
            <div className="skeleton block" />
          </div>
        )}

        {answer && (
          <article className="answerCard">
            <div className="answerHeader">
              <span className="answerIcon">A</span>

              <div>
                <h3>Grounded answer</h3>
                <p>
                  {sources.length} retrieved source{sources.length === 1 ? "" : "s"}
                </p>
              </div>

              <div className="answerActions">
                <button className="smallButton" onClick={() => copyText(answer, "Answer copied.")}>
                  Copy answer
                </button>

                <button className="smallButton subtle" onClick={handleClearQuestion}>
                  Clear
                </button>
              </div>
            </div>

            <div className="answerText">
              <AnswerBlocks answer={answer} />
            </div>
          </article>
        )}
      </div>
    </section>
  );
}