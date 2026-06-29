function renderInline(text) {
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    return part;
  });
}

export default function AnswerBlocks({ answer }) {
  const lines = String(answer || "").split("\n");

  return (
    <>
      {lines.map((line, index) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={index} className="answerSpacer" />;
        }

        const markdownHeading = trimmed.match(/^\*\*(.+?)\*\*:?\s*$/);

        if (markdownHeading) {
          return (
            <h4 key={index} className="answerSectionTitle">
              {markdownHeading[1].replace(/:$/, "")}
            </h4>
          );
        }

        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={index} className="answerSectionTitle">
              {renderInline(trimmed.replace(/^###\s+/, ""))}
            </h4>
          );
        }

        if (trimmed.startsWith("## ")) {
          return (
            <h4 key={index} className="answerSectionTitle">
              {renderInline(trimmed.replace(/^##\s+/, ""))}
            </h4>
          );
        }

        if (trimmed.startsWith("# ")) {
          return (
            <h4 key={index} className="answerSectionTitle">
              {renderInline(trimmed.replace(/^#\s+/, ""))}
            </h4>
          );
        }

        const bullet = trimmed.match(/^[-*]\s+(.+)$/);

        if (bullet) {
          return (
            <div key={index} className="answerBullet">
              <span>•</span>
              <p>{renderInline(bullet[1])}</p>
            </div>
          );
        }

        const numbered = trimmed.match(/^(\d+)[.)]\s+(.+)$/);

        if (numbered) {
          return (
            <div key={index} className="answerBullet numbered">
              <span>{numbered[1]}</span>
              <p>{renderInline(numbered[2])}</p>
            </div>
          );
        }

        return <p key={index}>{renderInline(trimmed)}</p>;
      })}
    </>
  );
}