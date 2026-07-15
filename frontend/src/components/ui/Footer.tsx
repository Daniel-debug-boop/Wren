import { Link } from "react-router";

interface FooterProps {
  version?: string;
  links?: Array<{ label: string; href: string }>;
}

export function Footer({ version = "1.30.0", links = [] }: FooterProps) {
  const defaultLinks = [
    { label: "Privacy", href: "/privacy" },
    { label: "Terms", href: "/terms" },
    {
      label: "GitHub",
      href: "https://github.com/wren-ai/wren",
      external: true,
    },
  ];

  const allLinks = links.length > 0 ? links : defaultLinks;

  return (
    <footer
      className="border-t border-border mt-auto"
      style={{ borderColor: "var(--border)" }}
      role="contentinfo"
    >
      <div className="mx-auto max-w-7xl px-6 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
          <p style={{ color: "var(--text-subtle)" }}>Wren v{version}</p>
          <nav aria-label="Footer navigation">
            <ul className="flex items-center gap-4 flex-wrap justify-center">
              {allLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    target={link.external ? "_blank" : undefined}
                    rel={link.external ? "noreferrer noopener" : undefined}
                    className="hover:underline underline-offset-2 transition-colors"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>
    </footer>
  );
}
