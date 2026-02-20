"use client";

import { useState } from "react";
import AskTab from "../components/tabs/AskTab";
import ImpactTab from "../components/tabs/ImpactTab";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("ask");

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 p-6">
      <h1 className="text-3xl font-bold">AI Codebase Guide</h1>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => setActiveTab("ask")}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            activeTab === "ask" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-300"
          }`}
        >
          Ask
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("impact")}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            activeTab === "impact"
              ? "bg-blue-600 text-white"
              : "bg-slate-800 text-slate-300"
          }`}
        >
          Impact
        </button>
      </div>

      <section className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        {activeTab === "ask" ? <AskTab /> : <ImpactTab />}
      </section>
    </main>
  );
}

