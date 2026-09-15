import type { Metadata } from 'next';
import { Amiri, Noto_Sans_Bengali } from 'next/font/google';
import './globals.css';

const arabicFont = Amiri({
  subsets: ['arabic'],
  weight: ['400', '700'],
  variable: '--font-arabic',
  display: 'swap',
});

const banglaFont = Noto_Sans_Bengali({
  subsets: ['bengali'],
  weight: ['400', '500', '700'],
  variable: '--font-bangla',
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Qur'an Topic Ayah Extractor",
  description:
    'একটি Topic দিলে পুরো কুরআন থেকে সেই বিষয়ের সাথে সম্পর্কিত আয়াত খুঁজে বের করার সিস্টেম',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bn" className={`${arabicFont.variable} ${banglaFont.variable}`}>
      <body className="bangla-text min-h-screen">{children}</body>
    </html>
  );
}
