/** @type {import('tailwindcss').Config} */
import typography from "@tailwindcss/typography";
export default {
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      colors: {
        accent: "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        text: "var(--text)",
        "text-muted": "var(--text-muted)",
        "text-subtle": "var(--text-subtle)",
        surface: "var(--surface)",
        "surface-hover": "var(--surface-hover)",
        border: "var(--border)",
        "border-strong": "var(--border-strong)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        full: "var(--radius-full)",
      },
      transitionTimingFunction: {
        spring: "var(--ease-spring)",
        out: "var(--ease-out)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
        glow: "var(--shadow-glow)",
        inner: "var(--shadow-inner)",
      },
    },
  },
  plugins: [typography],
};
