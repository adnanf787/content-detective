import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ReelScope — Instagram content research',
  description: 'Look closer at your Instagram videos. Local media inspection, creator insights, and source-backed claim research. No invented scores.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
