"use client"

import {
  Sparkles, FileSearch, GitCompare, BookOpenCheck, Quote, Library, BarChart3,
  ArrowRight, ArrowUpRight,
} from 'lucide-react';
import Link from "next/link";

const features = [
  { icon: FileSearch, title: 'Discover', desc: 'Semantic search across arXiv, journals & repositories.' },
  { icon: BookOpenCheck, title: 'Understand', desc: 'AI summaries, contributions & methodology extraction.' },
  { icon: GitCompare, title: 'Compare', desc: 'Side-by-side benchmark & architecture analysis.' },
  { icon: Quote, title: 'Evidence', desc: 'Citations, confidence scores & verified snippets.' },
  { icon: Library, title: 'Organize', desc: 'Collections, sources & literature review generation.' },
  { icon: BarChart3, title: 'Analytics', desc: 'Retrieval quality, faithfulness & system health.' },
];

const topics = [
  'Transformers', 'RAG', 'Diffusion Models', 'Reinforcement Learning', 'Multi-Agent Systems',
  'Mechanistic Interpretability', 'Vision-Language Models', 'Constitutional AI', 'Mixture of Experts',
  'Retrieval-Augmented Generation', 'Chain-of-Thought', 'LoRA Fine-tuning',
];

const floatingPapers = [
  { title: 'Attention Is All You Need', tag: 'Transformers', rotate: '-6deg', delay: '0s' },
  { title: 'Constitutional AI', tag: 'Alignment', rotate: '4deg', delay: '1.5s' },
  { title: 'Retrieval-Augmented Generation', tag: 'RAG', rotate: '-3deg', delay: '3s' },
];

export function LandingPanel({ onGetStarted }: { onGetStarted: () => void }) {
  return (
    <div className="relative h-full flex flex-col justify-center px-10 lg:px-16 xl:px-20 py-10 overflow-hidden">
      <div className="relative z-10 max-w-2xl">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass animate-fade-up mb-8">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span className="text-xs font-semibold text-slate-300 tracking-wide">Enterprise AI Research Platform</span>
          <span className="text-xs text-slate-500">·</span>
          <span className="text-xs font-medium text-indigo-300">v2.0</span>
        </div>

        {/* Editorial headline — mixed serif + sans */}
        <h1 className="text-5xl lg:text-6xl xl:text-7xl font-extrabold leading-[1.02] tracking-tight mb-6 animate-fade-up" style={{ animationDelay: '80ms' }}>
          <span className="text-gradient-soft">Research,</span>
          <br />
          <span className="font-serif-display italic text-gradient-ai animate-shine bg-[linear-gradient(110deg,#60A5FA,#818CF8,#C4B5FD,#60A5FA)] bg-clip-text text-transparent font-normal">
            reimagined
          </span>
          <span className="text-gradient-soft">.</span>
        </h1>

        <p className="text-base lg:text-lg text-slate-400 leading-relaxed mb-8 max-w-xl animate-fade-up" style={{ animationDelay: '160ms' }}>
          Discover, understand, compare, and synthesize research papers with an
          AI-native workspace built by researchers, for researchers.
        </p>

        {/* CTAs */}
        <div className="flex items-center gap-3 mb-12 animate-fade-up" style={{ animationDelay: '240ms' }}>
          <button
            onClick={onGetStarted}
            className="shimmer group inline-flex items-center gap-2 px-6 py-3.5 rounded-xl gradient-ai text-white text-sm font-semibold shadow-glow hover:shadow-glow-lg hover:-translate-y-0.5 active:translate-y-0 transition-all"
          >
            <Link
  href="/dashboard"
  
>   Get Started Free
</Link>
         
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </button>
          <button className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl glass-strong text-slate-200 text-sm font-semibold hover:bg-white/10 hover:-translate-y-0.5 transition-all">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-glow" />
            Watch Demo
          </button>
        </div>

        {/* Feature pills */}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 max-w-xl mb-10 animate-fade-up" style={{ animationDelay: '320ms' }}>
          {features.map((f) => (
            <div
              key={f.title}
              className="group p-4 rounded-2xl glass-card hover:bg-white/[0.08] hover:border-indigo-400/30 hover:-translate-y-1 transition-all duration-300"
            >
              <div className="w-9 h-9 rounded-lg gradient-ai-soft border border-indigo-400/20 flex items-center justify-center mb-3 group-hover:border-indigo-400/40 transition-colors">
                <f.icon className="w-4 h-4 text-indigo-300" strokeWidth={2} />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 mb-1">{f.title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        Logos
        <div className="flex items-center gap-5 text-xs animate-fade-up" style={{ animationDelay: '400ms' }}>
          <span className="font-semibold text-slate-500">Trusted by</span>
          {['MIT', 'Stanford', 'DeepMind', 'OpenAI', 'Anthropic'].map((l) => (
            <span key={l} className="font-bold text-slate-600 tracking-tight hover:text-slate-400 transition-colors">{l}</span>
          ))}
        </div>
      </div>

      {/* Floating paper cards — bottom right */}
      <div className="absolute bottom-8 right-8 lg:right-16 xl:right-20 hidden md:block pointer-events-none">
        <div className="relative w-64 h-48">
          {floatingPapers.map((p, i) => (
            <div
              key={p.title}
              className="absolute glass-card rounded-2xl p-4 shadow-soft animate-float"
              style={{
                transform: `rotate(${p.rotate})`,
                animationDelay: p.delay,
                top: `${i * 56}px`,
                right: `${i * 20}px`,
                width: '220px',
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-indigo-500/15 text-indigo-300">{p.tag}</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
              </div>
              <p className="text-xs font-semibold text-slate-200 leading-snug">{p.title}</p>
              <div className="mt-3 flex items-center gap-1.5">
                <div className="h-1 w-16 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full w-2/3 gradient-ai rounded-full" />
                </div>
                <span className="text-[10px] text-slate-500">analyzed</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Topic marquee — bottom strip */}
      <div className="absolute bottom-0 left-0 right-0 overflow-hidden border-t border-white/5 py-3">
        <div className="flex gap-8 animate-marquee whitespace-nowrap">
          {[...topics, ...topics].map((t, i) => (
            <span key={i} className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
              <Sparkles className="w-3 h-3 text-indigo-500/50" />
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/* Knowledge-graph constellation — decorative SVG */
export function Constellation() {
  const nodes = [
    { x: 50, y: 50, r: 5, label: 'AI' },
    { x: 20, y: 25, r: 3, label: 'NLP' },
    { x: 80, y: 20, r: 3, label: 'Vision' },
    { x: 15, y: 75, r: 3, label: 'RL' },
    { x: 85, y: 80, r: 3, label: 'RAG' },
    { x: 50, y: 12, r: 2.5, label: 'LLM' },
    { x: 65, y: 60, r: 2.5, label: '' },
    { x: 30, y: 55, r: 2, label: '' },
  ];
  const edges = [[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[1,5],[2,5],[3,7],[4,6],[6,7]];

  return (
    <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full opacity-40" preserveAspectRatio="xMidYMid slice">
      {edges.map(([a, b], i) => (
        <line
          key={i}
          x1={nodes[a].x} y1={nodes[a].y}
          x2={nodes[b].x} y2={nodes[b].y}
          stroke="url(#edgeGrad)"
          strokeWidth="0.15"
          className="animate-draw"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle
            cx={n.x} cy={n.y} r={n.r}
            fill="url(#nodeGrad)"
            className="animate-pulse-glow"
            style={{ animationDelay: `${i * 0.3}s` }}
          />
          {n.label && (
            <text x={n.x} y={n.y - n.r - 1.5} fontSize="2.5" fill="#94A3B8" textAnchor="middle" className="font-medium">
              {n.label}
            </text>
          )}
        </g>
      ))}
      <defs>
        <linearGradient id="edgeGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#6366F1" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.2" />
        </linearGradient>
        <radialGradient id="nodeGrad">
          <stop offset="0%" stopColor="#A78BFA" />
          <stop offset="100%" stopColor="#6366F1" stopOpacity="0.4" />
        </radialGradient>
      </defs>
    </svg>
  );
}

export function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative w-9 h-9 rounded-xl gradient-ai flex items-center justify-center shadow-glow">
        <Sparkles className="w-5 h-5 text-white" strokeWidth={2.2} />
        <div className="absolute inset-0 rounded-xl bg-indigo-500/20 blur-md -z-10" />
      </div>
      <span className="text-sm font-bold text-slate-100 tracking-tight">Research<span className="text-indigo-400">AI</span></span>
    </div>
  );
}
