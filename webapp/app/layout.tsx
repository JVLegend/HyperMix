import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://hypermix-observatory.vercel.app"),
  title: "HyperMix Observatory",
  description:
    "Explore an open benchmark for hyperspectral detection, calibrated uncertainty, and band sparsity.",
  openGraph: {
    title: "HyperMix Observatory",
    description: "Honest detection, calibration, and band-sparsity benchmark",
    images: [{ url: "/og-v2.png", width: 1672, height: 941 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HyperMix Observatory",
    description: "Honest detection, calibration, and band-sparsity benchmark",
    images: ["/og-v2.png"],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#f3f0e9",
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
        {children}
      </body>
    </html>
  );
}
