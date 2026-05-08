import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Condo Law Agent — New England Dashboard",
  description: "RAG dashboard for New England common interest counsel.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
