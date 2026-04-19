import type { Metadata } from "next"
import { Syne, DM_Sans, DM_Mono, Manrope } from "next/font/google"
import { AuthProvider } from "@/context/AuthContext"
import { UsageProvider } from "@/context/UsageContext"
import { AppStateProvider } from "@/context/AppStateContext"
import "./globals.css"

const syne = Syne({ subsets: ["latin"], weight: ["400","500","600","700","800"], variable: "--font-syne", display: "swap" })
const dmSans = DM_Sans({ subsets: ["latin"], weight: ["300","400","500","600","700"], variable: "--font-dm-sans", display: "swap" })
const dmMono = DM_Mono({ subsets: ["latin"], weight: ["300","400","500"], variable: "--font-dm-mono", display: "swap" })
const manrope = Manrope({ subsets: ["latin"], weight: ["400","500","600","700","800"], variable: "--font-manrope", display: "swap" })

export const metadata: Metadata = {
  title: "TubeQuery — Ask anything about any video",
  description: "AI-powered YouTube research assistant with timestamped citations",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${syne.variable} ${dmSans.variable} ${dmMono.variable} ${manrope.variable}`}>
      <body style={{ fontFamily: "var(--font-dm-sans), sans-serif" }}>
        <AuthProvider>
          <UsageProvider>
            <AppStateProvider>
              {children}
            </AppStateProvider>
          </UsageProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
