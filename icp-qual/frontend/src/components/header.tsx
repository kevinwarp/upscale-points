import { Logo } from "./logo";

export function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-[var(--border)]">
      <div className="max-w-[1200px] mx-auto flex items-center justify-between h-16 px-6 md:px-10">
        {/* Logo + tagline */}
        <a
          href="https://upscale.ai"
          target="_blank"
          rel="noopener noreferrer"
          className="flex flex-col gap-0.5 no-underline"
        >
          <Logo />
          <span className="text-[0.58rem] text-[var(--muted)] tracking-wide font-medium whitespace-nowrap">
            AI Creative + Media + Measurement &mdash; One Platform
          </span>
        </a>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-7">
          <a href="https://upscale.ai/how-it-works" target="_blank" rel="noopener noreferrer" className="text-[0.85rem] font-medium text-[var(--navy)] no-underline hover:text-[var(--pink)] transition-colors">
            Platform
          </a>
          <a href="https://upscale.ai/solutions" target="_blank" rel="noopener noreferrer" className="text-[0.85rem] font-medium text-[var(--navy)] no-underline hover:text-[var(--pink)] transition-colors">
            Solutions
          </a>
          <a href="https://upscale.ai/solutions#case-studies" target="_blank" rel="noopener noreferrer" className="text-[0.85rem] font-medium text-[var(--navy)] no-underline hover:text-[var(--pink)] transition-colors">
            Case Studies
          </a>
          <a href="https://upscale.ai/about" target="_blank" rel="noopener noreferrer" className="text-[0.85rem] font-medium text-[var(--navy)] no-underline hover:text-[var(--pink)] transition-colors">
            About
          </a>
          <a href="https://upscale.ai/careers" target="_blank" rel="noopener noreferrer" className="text-[0.85rem] font-medium text-[var(--navy)] no-underline hover:text-[var(--pink)] transition-colors">
            Careers
          </a>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <span className="hidden lg:inline text-[0.8rem] font-medium text-[var(--muted)]">
            ICP Qualification Pipeline
          </span>
          <a
            href="https://upscale.ai/contact"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-5 py-2 bg-[var(--navy)] text-white text-[0.82rem] font-semibold rounded-lg no-underline hover:bg-[var(--dark-teal)] transition-colors"
          >
            Get Demo
          </a>
        </div>
      </div>
    </header>
  );
}
