export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const SOURCE_TABS = [
  { id: "text", label: "Text", hint: "Paste notes, docs, snippets" },
  { id: "file", label: "File", hint: "PDF, TXT, DOCX, PPTX" },
  { id: "url", label: "Website", hint: "Extract readable page text" },
  { id: "youtube", label: "YouTube", hint: "Use video transcript" },
];

export const PERSONAS = [
  { value: "student", label: "Student" },
  { value: "developer", label: "Developer" },
  { value: "interviewer", label: "Interviewer" },
  { value: "concise", label: "Concise" },
];

export const EXAMPLE_QUESTIONS = [
  "Summarize the key idea from this collection.",
  "Explain this like I am preparing for an interview.",
  "What are the most important points from the sources?",
  "Give me possible interview questions from this content.",
];