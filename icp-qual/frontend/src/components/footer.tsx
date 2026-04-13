import { Logo } from "./logo";

function SocialIcon({ href, title, children }: { href: string; title: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      title={title}
      className="flex items-center justify-center w-9 h-9 rounded-full bg-[var(--bg-grey)] text-[var(--navy)] no-underline hover:bg-[var(--pink-light)] transition-colors"
    >
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
        {children}
      </svg>
    </a>
  );
}

export function Footer() {
  return (
    <footer className="mt-20">
      {/* CTA banner */}
      <div className="mx-6 md:mx-10 mb-8">
        <div className="bg-[var(--navy)] rounded-[20px] py-12 px-8 text-center">
          <h3 className="text-white text-2xl font-bold tracking-tight mb-2">
            Ready to unlock the power of AI advertising on Streaming TV?
          </h3>
          <p className="text-white/65 text-[0.95rem] mb-5">
            See how Upscale.ai drives measurable performance for eCommerce brands.
          </p>
          <a
            href="https://upscale.ai/contact"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-7 py-3 bg-white text-[var(--navy)] text-[0.9rem] font-semibold rounded-[10px] no-underline hover:-translate-y-px hover:shadow-lg transition-all"
          >
            Get Demo &rarr;
          </a>
        </div>
      </div>

      {/* Bottom section */}
      <div className="px-6 md:px-10 pt-6 pb-3 text-center">
        {/* Nav */}
        <nav className="flex justify-center gap-6 mb-5">
          <a href="https://upscale.ai/how-it-works" target="_blank" rel="noopener noreferrer" className="text-[var(--navy)] no-underline text-[0.82rem] font-medium hover:text-[var(--pink)]">
            Platform
          </a>
          <a href="https://upscale.ai/solutions" target="_blank" rel="noopener noreferrer" className="text-[var(--navy)] no-underline text-[0.82rem] font-medium hover:text-[var(--pink)]">
            Solutions
          </a>
          <a href="https://upscale.ai/about" target="_blank" rel="noopener noreferrer" className="text-[var(--navy)] no-underline text-[0.82rem] font-medium hover:text-[var(--pink)]">
            About
          </a>
          <a href="https://upscale.ai/careers" target="_blank" rel="noopener noreferrer" className="text-[var(--navy)] no-underline text-[0.82rem] font-medium hover:text-[var(--pink)]">
            Careers
          </a>
          <a href="https://upscale.ai/contact" target="_blank" rel="noopener noreferrer" className="text-[var(--navy)] no-underline text-[0.82rem] font-medium hover:text-[var(--pink)]">
            Get Demo
          </a>
        </nav>

        {/* Social icons */}
        <div className="flex justify-center gap-4 mb-5">
          <SocialIcon href="https://www.instagram.com/upscaleaihq" title="Instagram">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
          </SocialIcon>
          <SocialIcon href="https://www.linkedin.com/company/upscaleaihq/" title="LinkedIn">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
          </SocialIcon>
          <SocialIcon href="https://x.com/upscaleaiHQ" title="X">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
          </SocialIcon>
          <SocialIcon href="https://www.facebook.com/upscaleaihq" title="Facebook">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
          </SocialIcon>
          <SocialIcon href="https://www.youtube.com/@TVAdsAI" title="YouTube">
            <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </SocialIcon>
          <SocialIcon href="https://vimeo.com/upscaleai" title="Vimeo">
            <path d="M23.977 6.416c-.105 2.338-1.739 5.543-4.894 9.609-3.268 4.247-6.026 6.37-8.29 6.37-1.409 0-2.578-1.294-3.553-3.881L5.322 11.4C4.603 8.816 3.834 7.522 3.01 7.522c-.179 0-.806.378-1.881 1.132L0 7.197c1.185-1.044 2.351-2.084 3.501-3.128C5.08 2.701 6.266 1.984 7.055 1.91c1.867-.18 3.016 1.1 3.447 3.838.465 2.953.789 4.789.971 5.507.539 2.45 1.131 3.674 1.776 3.674.502 0 1.256-.796 2.265-2.385 1.004-1.589 1.54-2.797 1.612-3.628.144-1.371-.395-2.061-1.614-2.061-.574 0-1.167.121-1.777.391 1.186-3.868 3.434-5.757 6.762-5.637 2.473.06 3.628 1.664 3.493 4.797l-.013.01z"/>
          </SocialIcon>
        </div>

        {/* Wordmark */}
        <div className="flex justify-center mb-4 opacity-50">
          <Logo size="small" />
        </div>

        {/* Legal */}
        <div className="flex justify-center gap-5 mb-2">
          <a href="https://upscale.ai/privacy" target="_blank" rel="noopener noreferrer" className="text-[var(--muted)] no-underline text-[0.78rem] hover:text-[var(--navy)]">
            Privacy
          </a>
          <a href="https://upscale.ai/terms" target="_blank" rel="noopener noreferrer" className="text-[var(--muted)] no-underline text-[0.78rem] hover:text-[var(--navy)]">
            Terms of Use
          </a>
        </div>

        <p className="text-[var(--muted)] text-[0.72rem] pb-4">
          &copy; {new Date().getFullYear()} Upscale.ai &middot; AI-Driven Performance Creative for Streaming TV
        </p>
      </div>
    </footer>
  );
}
