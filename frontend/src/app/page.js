"use client";

import { useEffect, useRef, useState } from "react";

import { request } from "./lib/api";

import ChatPanel from "./components/ChatPanel";
import EvidencePanel from "./components/EvidencePanel";
import Sidebar from "./components/Sidebar";
import Toast from "./components/Toast";
import Topbar from "./components/Topbar";

export default function Home() {
  const [collectionName, setCollectionName] = useState("dsa-placement-master");
  const [activeTab, setActiveTab] = useState("text");

  const [sourceName, setSourceName] = useState("dsa_notes");
  const [rawText, setRawText] = useState("");
  const [url, setUrl] = useState("");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [file, setFile] = useState(null);

  const [question, setQuestion] = useState("");
  const [persona, setPersona] = useState("student");
  const [topK, setTopK] = useState(3);

  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [stats, setStats] = useState(null);
  const [collections, setCollections] = useState([]);
  const [health, setHealth] = useState("checking");

  const [ingestLoading, setIngestLoading] = useState(false);
  const [queryLoading, setQueryLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [activity, setActivity] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);

  const answerRef = useRef(null);

  function pushActivity(type, message) {
    setActivity((prev) =>
      [
        {
          id: crypto.randomUUID(),
          type,
          message,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
        ...prev,
      ].slice(0, 6)
    );
  }

  function showToast(type, message) {
    setToast({ type, message });
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => setToast(null), 4200);
  }

  async function copyText(text, successMessage = "Copied.") {
    if (!text) {
      showToast("error", "Nothing to copy.");
      return;
    }

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      showToast("success", successMessage);
    } catch {
      showToast("error", "Copy failed.");
    }
  }

  async function loadHealth() {
    try {
      const data = await request("/health");
      setHealth(data.database === "ok" ? "online" : "degraded");
    } catch {
      setHealth("offline");
    }
  }

  async function loadCollections() {
    try {
      const data = await request("/collections");
      setCollections(Array.isArray(data.collections) ? data.collections : []);
    } catch {
      setCollections([]);
    }
  }

  async function loadStats(name = collectionName) {
    if (!name.trim()) return;

    try {
      const data = await request(`/collections/${encodeURIComponent(name)}/stats`);
      setStats(data);
    } catch {
      setStats(null);
    }
  }

  useEffect(() => {
    loadHealth();
    loadCollections();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => loadStats(collectionName), 400);
    return () => clearTimeout(timer);
  }, [collectionName]);

  useEffect(() => {
    if (!collectionName.trim()) return;

    try {
      const stored = localStorage.getItem(`rag-memory:${collectionName.trim()}`);
      setChatHistory(stored ? JSON.parse(stored) : []);
    } catch {
      setChatHistory([]);
    }
  }, [collectionName]);

  useEffect(() => {
    if (!collectionName.trim()) return;

    localStorage.setItem(
      `rag-memory:${collectionName.trim()}`,
      JSON.stringify(chatHistory.slice(-8))
    );
  }, [chatHistory, collectionName]);

  async function handleIngest() {
    const collection = collectionName.trim();

    if (!collection) {
      showToast("error", "Collection name is required.");
      return;
    }

    setIngestLoading(true);

    try {
      let data;

      if (activeTab === "text") {
        if (!rawText.trim()) throw new Error("Paste some text before ingesting.");

        data = await request("/ingest/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            collection_name: collection,
            source_name: sourceName.trim() || "pasted_text",
            text: rawText,
          }),
        });
      }

      if (activeTab === "file") {
        if (!file) throw new Error("Choose a file first.");

        const form = new FormData();
        form.append("collection_name", collection);
        form.append("source_name", sourceName.trim() || file.name);
        form.append("file", file);

        data = await request("/ingest/file", {
          method: "POST",
          body: form,
        });
      }

      if (activeTab === "url") {
        if (!url.trim()) throw new Error("Enter a website URL.");

        data = await request("/ingest/url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            collection_name: collection,
            url: url.trim(),
          }),
        });
      }

      if (activeTab === "youtube") {
        if (!youtubeUrl.trim()) throw new Error("Enter a YouTube URL.");

        data = await request("/ingest/youtube", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            collection_name: collection,
            url: youtubeUrl.trim(),
          }),
        });
      }

      const added = data?.chunks_added ?? 0;
      const msg =
        added === 0
          ? "Duplicate source skipped."
          : `Ingested ${added} chunk${added === 1 ? "" : "s"}.`;

      showToast(added === 0 ? "info" : "success", msg);
      pushActivity("ingest", `${msg} Collection: ${data?.collection_name || collection}`);
      await loadCollections();
      await loadStats(collection);
    } catch (err) {
      showToast("error", err.message);
      pushActivity("error", err.message);
    } finally {
      setIngestLoading(false);
    }
  }

  async function handleAsk() {
    const collection = collectionName.trim();

    if (!collection) {
      showToast("error", "Collection name is required.");
      return;
    }

    if (!question.trim()) {
      showToast("error", "Ask a question first.");
      return;
    }

    setQueryLoading(true);
    setAnswer("");
    setSources([]);

    try {
      const data = await request("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          collection_name: collection,
          question: question.trim(),
          top_k: Number(topK),
          persona,
          chat_history: chatHistory.slice(-6),
        }),
      });

      setAnswer(data.answer || "");
      setSources(Array.isArray(data.sources) ? data.sources : []);

      setChatHistory((prev) =>
        [
          ...prev,
          { role: "user", content: question.trim() },
          { role: "assistant", content: data.answer || "" },
        ].slice(-8)
      );

      pushActivity("query", `Asked: ${question.trim().slice(0, 80)}`);

      window.setTimeout(
        () => answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        80
      );
    } catch (err) {
      showToast("error", err.message);
      pushActivity("error", err.message);
    } finally {
      setQueryLoading(false);
    }
  }

  function handleClearQuestion() {
    setQuestion("");
    setAnswer("");
    setSources([]);
    pushActivity("clear", "Cleared question and answer.");
  }

  function handleClearMemory() {
    const key = `rag-memory:${collectionName.trim()}`;
    setChatHistory([]);
    localStorage.removeItem(key);
    pushActivity("clear", "Cleared conversation memory.");
    showToast("success", "Conversation memory cleared.");
  }

  async function handleDeleteCollection() {
    const collection = collectionName.trim();
    if (!collection) return;

    const ok = window.confirm(`Delete collection "${collection}" and all its chunks?`);
    if (!ok) return;

    try {
      await request(`/collections/${encodeURIComponent(collection)}`, { method: "DELETE" });
      showToast("success", "Collection deleted.");
      pushActivity("delete", `Deleted collection: ${collection}`);
      setStats(null);
      setAnswer("");
      setSources([]);
      setChatHistory([]);
      localStorage.removeItem(`rag-memory:${collection}`);
      await loadCollections();
    } catch (err) {
      showToast("error", err.message);
    }
  }

  return (
    <main className="shell">
      <div className="ambient ambientOne" />
      <div className="ambient ambientTwo" />

      <Toast toast={toast} />

      <Topbar
        health={health}
        onRefresh={() => {
          loadHealth();
          loadCollections();
          loadStats();
        }}
      />

      <section className="workspace">
        <Sidebar
          collectionName={collectionName}
          setCollectionName={setCollectionName}
          collections={collections}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          sourceName={sourceName}
          setSourceName={setSourceName}
          rawText={rawText}
          setRawText={setRawText}
          url={url}
          setUrl={setUrl}
          youtubeUrl={youtubeUrl}
          setYoutubeUrl={setYoutubeUrl}
          file={file}
          setFile={setFile}
          ingestLoading={ingestLoading}
          handleIngest={handleIngest}
          handleDeleteCollection={handleDeleteCollection}
        />

        <ChatPanel
          question={question}
          setQuestion={setQuestion}
          persona={persona}
          setPersona={setPersona}
          topK={topK}
          setTopK={setTopK}
          answer={answer}
          sources={sources}
          queryLoading={queryLoading}
          handleAsk={handleAsk}
          handleClearQuestion={handleClearQuestion}
          handleClearMemory={handleClearMemory}
          chatHistory={chatHistory}
          copyText={copyText}
          answerRef={answerRef}
        />

        <EvidencePanel stats={stats} sources={sources} activity={activity} copyText={copyText} />
      </section>
    </main>
  );
}