import "./globals.css";
import PersistentShell from "../components/PersistentShell";
import type { ReactNode } from "react";

export const metadata = {
  title: "Kosmos",
  description: "Kosmos LMS — local-first Life Management System",
};

// RootLayout stays a Server Component so Next 16 `metadata` export works;
// all interactive shell chrome (top bar, drawer, sidebar, banner) lives
// in the client-side `<PersistentShell>` wrapper.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="nagtang">
      <body>
        <PersistentShell>{children}</PersistentShell>
      </body>
    </html>
  );
}
