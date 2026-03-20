import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Chess Analyzer",
  description: "Analyze your Chess.com games, discover weaknesses, and get AI coaching",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <header className="border-b border-chess-surface-light bg-chess-medium/80 backdrop-blur-sm sticky top-0 z-40">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
            <Link href="/" className="flex items-center gap-2 text-white transition-colors hover:text-chess-gold">
              <span className="text-2xl">♟</span>
              <span className="text-lg font-bold">Chess Analyzer</span>
            </Link>
            <span className="hidden text-sm text-gray-500 sm:block">
              AI-Powered Game Analysis
            </span>
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
