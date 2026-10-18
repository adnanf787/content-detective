import { z } from 'zod';
import type { Source } from './types';
export const researchSchema = z.object({ query: z.string().trim().min(3).max(180), language: z.enum(['en', 'ur']).default('en') }).strict();
export function plainText(input: string) {
  return input.replace(/<[^>]*>/g, '').replace(/&quot;/g, '"').replace(/&#039;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').slice(0, 1000);
}
export function normalizeSources(pages: unknown, language: 'en' | 'ur', now = new Date().toISOString()): Source[] {
  if (!Array.isArray(pages)) return [];
  return pages.slice(0, 5).flatMap((page: unknown) => {
    if (!page || typeof page !== 'object') return [];
    const value = page as Record<string, unknown>;
    if (typeof value.key !== 'string' || typeof value.title !== 'string') return [];
    return [{ title: plainText(value.title), url: `https://${language}.wikipedia.org/wiki/${encodeURIComponent(value.key)}`,
      excerpt: plainText(typeof value.excerpt === 'string' ? value.excerpt : typeof value.description === 'string' ? value.description : ''),
      publisher: `${language === 'ur' ? 'Urdu' : 'English'} Wikipedia · reference context`, retrievedAt: now }];
  });
}
