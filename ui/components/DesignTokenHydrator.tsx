"use client";
import { useEffect } from "react";
import { kernelClient } from "../lib/kernel-client";

// On mount, fetch the merged design tokens from /api/kernel/design-tokens
// and set each as a CSS custom property on the document root, so any
// plugin-registered token (e.g. `--praxis-accent`) is available to Tailwind
// v4's `@theme` layer without a rebuild. The static Tibetan Five-Wisdom
// palette in globals.css remains the authoritative default; kernel tokens
// override wherever both define the same property name.
export default function DesignTokenHydrator() {
  useEffect(() => {
    let cancelled = false;
    kernelClient
      .getDesignTokens()
      .then((tokens) => {
        if (cancelled) return;
        const root = document.documentElement;
        for (const [name, value] of Object.entries(tokens)) {
          // Kernel tokens arrive as "--praxis-accent": "oklch(…)" already
          // in CSS-custom-property form; guard anyway.
          const key = name.startsWith("--") ? name : `--${name}`;
          root.style.setProperty(key, String(value));
        }
        root.setAttribute("data-tokens-hydrated", "true");
      })
      .catch(() => {
        document.documentElement.setAttribute("data-tokens-hydrated", "failed");
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return null;
}
