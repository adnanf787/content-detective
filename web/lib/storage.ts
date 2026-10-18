import type { Report } from './types';
const KEY = 'reelscope.saved.v1';
export function loadReports(): Report[] {
  try { const data = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(data) ? data.filter(r => r && typeof r.id === 'string' && typeof r.transcript === 'string' && Array.isArray(r.observations) && Array.isArray(r.claims)).slice(0, 20) : []; }
  catch { return []; }
}
export function saveReports(reports: Report[]) {
  // Save only on explicit user action. Original media and frame images are excluded.
  const compact = reports.slice(0, 20).map(r => ({ ...r, media: r.media ? { ...r.media, frames: [] } : null }));
  try { localStorage.setItem(KEY, JSON.stringify(compact)); }
  catch { throw new Error('Browser storage is full or unavailable. Export a report or remove an older saved study.'); }
}
