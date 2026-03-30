import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "家庭健康检查单管理",
  description: "结构化存储与趋势跟踪",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
