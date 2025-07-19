"use client";
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function LayoutClientWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (pathname.startsWith('/dashboard') && !token) {
      router.push('/login');
    }
  }, [pathname, router]);
  return <>{children}</>;
} 