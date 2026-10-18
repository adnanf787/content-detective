export type Frame = { time: number; image: string; brightness: number };
export type MediaInfo = {
  name: string; size: number; type: string; duration: number;
  width: number; height: number; frames: Frame[];
};
export type Source = { title: string; url: string; excerpt: string; publisher: string; retrievedAt: string };
export type Claim = { id: string; text: string; reason: string; status: 'Needs verification'; sources: Source[]; researchQuery?: string };
export type Observation = { title: string; evidence: string; suggestion: string; category: 'Content' | 'Delivery' | 'Format' | 'Trust' };
export type Report = {
  id: string; name: string; createdAt: string; instagramUrl: string; goal: string;
  transcript: string; transcriptSource: 'manual' | 'local-whisper' | 'none'; language: string;
  media: MediaInfo | null;
  wordCount: number; sentenceCount: number; wordsPerMinute: number | null;
  opening: string; keywords: { term: string; count: number }[]; hashtags: string[];
  observations: Observation[]; claims: Claim[]; limitations: string[];
};
