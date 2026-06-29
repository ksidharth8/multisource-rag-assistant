import "./globals.css";

export const metadata = {
  title: "MultiSource RAG Assistant",
  description:
    "A production-style RAG assistant using Next.js, FastAPI, Supabase pgvector, Sentence Transformers, and Groq.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}