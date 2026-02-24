const FOOTER_LINKS = ["Privacy", "Terms", "Docs", "Status"];

export default function Footer() {
  return (
    <footer className="py-12 px-6 bg-base border-t border-white/[0.05]">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center font-black text-xs bg-gradient-brand text-base">
              FF
            </div>
            <span className="font-bold text-base font-mono text-snow">
              FixFlow AI
            </span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6">
            {FOOTER_LINKS.map((item) => (
              <a
                key={item}
                href="#"
                className="text-xs font-mono text-slate hover:text-mint transition-colors duration-200"
              >
                {item}
              </a>
            ))}
          </div>

          {/* Copyright */}
          <p className="text-xs font-mono text-slate">
            © 2025 FixFlow AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
