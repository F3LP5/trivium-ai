import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { ZoomProvider } from "@/context/ZoomContext";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Trivium - Autonomous AI Education",
  description: "Gerador autônomo e estruturado de matrizes curriculares e aulas com rigor acadêmico",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ZoomProvider>
          {children}
        </ZoomProvider>
      </body>
    </html>
  );
}
