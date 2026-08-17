import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "TrendCraft — Content Intelligence",
    template: "%s · TrendCraft",
  },
  description:
    "Discover emerging short-form video formats, understand why they work, and turn them into shootable scenarios.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bloom min-h-dvh antialiased">{children}</body>
    </html>
  );
}
