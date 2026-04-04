import { Navbar } from "./Navbar";

interface PageLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export function PageLayout({ children, title }: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 pt-20 pb-10">
        {title && (
          <h1 className="mb-6 text-2xl font-bold text-gray-900">{title}</h1>
        )}
        {children}
      </main>
    </div>
  );
}
