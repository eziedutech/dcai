import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import { Scene } from "@/components/motion";
import { LangProvider } from "@/lib/i18n";
import "./globals.css";

// Plus Jakarta Sans was drawn for Jakarta; one family carries the whole interface.
const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: { default: "dcAI · Digital Citizenship AI", template: "%s | dcAI" },
  description:
    "Digital Citizenship AI, Family Safety Guardian: guidance for children aged 10 to 17 in the moment, and insight for parents.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="id" className={jakarta.variable}>
      <body className="min-h-dvh">
        <Scene />
        <LangProvider>{children}</LangProvider>
      </body>
    </html>
  );
}
