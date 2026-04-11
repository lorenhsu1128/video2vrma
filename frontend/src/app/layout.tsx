export const metadata = {
  title: "video2vrma",
  description: "MP4 影片轉 VRMA 動畫",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
