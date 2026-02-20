import "./globals.css";

export const metadata = {
  title: "AI Codebase Guide",
  description: "Full-stack scaffold for AI Codebase Guide",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}

