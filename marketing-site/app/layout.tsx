import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Upstream - Early-Warning Payer Risk Intelligence",
  description: "Early-warning payer behavioral drift detection for dialysis, ABA therapy, imaging, and home health agencies.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
