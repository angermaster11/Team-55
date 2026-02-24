import type { Feature, Step, FAQ, NavLink } from "./types";

export const NAV_LINKS: NavLink[] = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export const FEATURES: Feature[] = [
  {
    icon: "⚡",
    title: "Instant Analysis",
    desc: "Connect your GitHub repo and get a full code quality report in under 60 seconds.",
    color: "#00FFB2",
  },
  {
    icon: "🔍",
    title: "Deep Code Review",
    desc: "AI scans every file, identifies anti-patterns, memory leaks, and logical errors.",
    color: "#7B61FF",
  },
  {
    icon: "🛠️",
    title: "Auto-Fix PRs",
    desc: "Get ready-to-merge pull requests with fixes applied automatically to your branch.",
    color: "#FF6B35",
  },
  {
    icon: "📊",
    title: "Quality Score",
    desc: "Track your repo health over time with detailed metrics and trend graphs.",
    color: "#00FFB2",
  },
  {
    icon: "🔒",
    title: "Security Audit",
    desc: "Detect CVEs, exposed secrets, and OWASP vulnerabilities before they ship.",
    color: "#7B61FF",
  },
  {
    icon: "🤝",
    title: "Team Sync",
    desc: "Assign fixes to teammates, leave comments, and resolve issues collaboratively.",
    color: "#FF6B35",
  },
];

export const STEPS: Step[] = [
  { num: "01", title: "Connect GitHub", desc: "OAuth with one click — no tokens, no config." },
  { num: "02", title: "Select Repository", desc: "Pick any public or private repo from your account." },
  { num: "03", title: "AI Analyses Code", desc: "Our engine reads every commit, file, and diff." },
  { num: "04", title: "Receive Fixes", desc: "Get annotated fixes as PRs or inline suggestions." },
];

export const FAQS: FAQ[] = [
  {
    q: "Is my private repository code safe?",
    a: "Yes. We never store your source code. Analysis is done in isolated, ephemeral containers that are destroyed immediately after. Only the analysis report is retained.",
  },
  {
    q: "Which languages are supported?",
    a: "JavaScript, TypeScript, Python, Go, Rust, Java, C++, Ruby, and PHP are fully supported. More languages are added monthly.",
  },
  {
    q: "Does it work with monorepos?",
    a: "Absolutely. FixFlow AI intelligently scopes analysis to changed files or specific packages, keeping feedback fast even for large monorepos.",
  },
  {
    q: "Can I integrate this into my CI/CD pipeline?",
    a: "Yes — we provide a GitHub Action and a REST API so you can trigger scans on every PR automatically.",
  },
  {
    q: "What's the difference between the free and pro plans?",
    a: "Free supports up to 3 public repos with basic checks. Pro unlocks private repos, security audits, team collaboration, and priority queue.",
  },
];

export const TERMINAL_LINES = [
  { text: "$ fixflowai scan github.com/user/my-project", color: "#00FFB2" },
  { text: "  → Fetching repository metadata...", color: "#6B7280" },
  { text: "  → Cloning HEAD commit (a3f1c2b)...", color: "#6B7280" },
  { text: "  → Running AST analysis on 147 files...", color: "#6B7280" },
  { text: "  ✓ Found 12 issues  (3 critical, 9 warnings)", color: "#FF6B35" },
  { text: "  ✓ Generating fixes...", color: "#6B7280" },
  { text: "  ✓ Pull request created: #42 — 'fix: AI corrections'", color: "#00FFB2" },
  { text: "  → Done in 34.2s", color: "#7B61FF" },
];

export const STATS = [
  { val: "2M+", label: "Lines Fixed" },
  { val: "99.1%", label: "Accuracy" },
  { val: "< 60s", label: "Avg. Scan Time" },
];

export const HERO_WORDS = ["Smarter.", "Faster.", "Cleaner."];
