export type Row = Record<string, string | number | boolean | null>;
export type Filters = {
  brands: string[];
  metric: string;
  minimum_group_n: number;
  publication_start?: string;
  publication_end?: string;
  min_age_days?: number | null;
  max_age_days?: number | null;
};
export type Workspace = {
  raw: Row[];
  comments: Row[];
  manifest: Record<string, string>;
  collection_report?: Record<string, unknown>;
};
export type Recommendation = {
  kind: string;
  action: string;
  evidence: string;
  limitations: string;
  confidence: string;
  examples?: { group: string; url: string; value: number }[];
};
export type Study = {
  posts: Row[];
  comments: Row[];
  tables: Record<string, Row[]>;
  summary: {
    posts: number;
    brands: number;
    comments_sampled: number;
    valid_metric_posts: number;
    limitations: string[];
    age_comparability: { shared_age_range_exists: boolean };
    comment_cue_counts: Record<string, number>;
  };
  questions: Row[];
  quality: Record<string, unknown>;
  manifest: Record<string, string>;
  metric_coverage: Row[];
  filters: Filters;
  recommendations: Recommendation[];
  available_brands: string[];
  measures: Record<string, string>;
  measure_notes: Record<string, string>;
  data_label: string;
  mixed_tracks: boolean;
  collection_report?: Record<string, unknown>;
  verification: unknown;
  collection_config: Record<string, unknown>;
  workspace?: Workspace;
};
export const DEFAULT_FILTERS: Filters = {
  brands: ["Jazz", "Ufone", "Zong"],
  metric: "visible_per_1000_views",
  minimum_group_n: 5,
};
export const LABEL_FIELDS = [
  "content_type",
  "topic",
  "caption_sentiment",
  "caption_language",
  "creative_angle",
  "local_context",
] as const;
export const LABEL_OPTIONS: Record<string, string[]> = {
  content_type: ["", "video", "reel", "image", "carousel"],
  caption_sentiment: ["", "positive", "neutral", "negative"],
  caption_language: ["", "Urdu", "Roman Urdu", "English", "Mixed", "Other"],
  creative_angle: [
    "",
    "Tutorial / how-to",
    "Humour",
    "Storytelling",
    "Product demo",
    "Offer / promotion",
    "Question / conversation",
    "Other",
  ],
  local_context: [
    "",
    "Everyday",
    "Eid",
    "Ramadan",
    "PSL / cricket",
    "Wedding season",
    "National occasion",
    "Other",
  ],
};
export function number(value: unknown, digits = 1): string {
  if (value === null || value === undefined || value === "") return "N/A";
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed.toLocaleString("en", { maximumFractionDigits: digits })
    : "N/A";
}
export function label(key: string) {
  return key.replaceAll("_", " ").replace(/^./, (s) => s.toUpperCase());
}
export function sourceUrl(value: unknown): string | null {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}
export async function request<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
    cache: "no-store",
  });
  if (!response.ok) {
    let detail =
      "The research service could not complete this request. Please try again.";
    try {
      const error = await response.json();
      if (typeof error.detail === "string") detail = error.detail;
    } catch {
      /* A platform error may return HTML. */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}
export async function download(body: unknown): Promise<void> {
  const response = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    throw new Error(result.detail || "Export failed. Please try again.");
  }
  const file = await response.blob();
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download =
    response.headers
      .get("Content-Disposition")
      ?.match(/filename="([^"]+)"/)?.[1] || "research-export";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}
