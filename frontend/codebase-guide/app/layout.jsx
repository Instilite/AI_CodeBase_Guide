import './globals.css'

export const metadata = {
  title: 'Codebase Guide',
  description: 'AI-powered codebase exploration',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
