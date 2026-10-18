import type { Metadata } from "next";
import "./dashboard.css";
import "./polish.css";

export const metadata: Metadata = {
  title: "Content Detective — Pakistan Telecom Research",
  description:
    "Explore verified YouTube observations, review content and public comments, compare engagement, and export the evidence behind your next content experiment.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dusk">
      <body>{children}</body>
    </html>
  );
}
