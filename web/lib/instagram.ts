export type InstagramSource = { url: string; shortcode: string; kind: 'reel' | 'post' | 'video' };

export function parseInstagramUrl(input: string): InstagramSource {
  let url: URL;
  try { url = new URL(input.trim()); } catch { throw new Error('Paste a complete Instagram Reel or post link, starting with https://.'); }
  if (url.protocol !== 'https:' || !['instagram.com', 'www.instagram.com', 'm.instagram.com'].includes(url.hostname) || url.username || url.password || url.port) {
    throw new Error('Use an https://www.instagram.com/reel/… or /p/… link. Other hosts are not accepted.');
  }
  const match = url.pathname.match(/^\/(reel|reels|p|tv)\/([a-zA-Z0-9_-]{3,80})\/?$/);
  if (!match) throw new Error('This is not a Reel or post link. Profiles, private messages, and Stories are not supported.');
  const kind = match[1] === 'p' ? 'post' : match[1] === 'tv' ? 'video' : 'reel';
  return { url: `https://www.instagram.com/${kind === 'reel' ? 'reel' : kind === 'post' ? 'p' : 'tv'}/${match[2]}/`, shortcode: match[2], kind };
}
