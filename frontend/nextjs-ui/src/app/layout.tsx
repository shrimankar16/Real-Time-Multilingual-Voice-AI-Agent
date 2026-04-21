import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Voice AI Agent - Clinical Appointment Booking',
  description: 'Real-time multilingual voice AI agent for booking doctor appointments',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
