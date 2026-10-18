"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowSquareOut,
  ChartLineUp,
  CheckCircle,
  Database,
  DownloadSimple,
  FileCsv,
  Funnel,
  GlobeHemisphereEast,
  Info,
  MagnifyingGlass,
  ChatCircleText,
  Lightbulb,
  List,
  Play,
  ShieldCheck,
  SpinnerGap,
  SquaresFour,
  UploadSimple,
  X,
  BookOpen,
  ArrowsClockwise,
} from "@phosphor-icons/react";
import {
  DEFAULT_FILTERS,
  LABEL_FIELDS,
  LABEL_OPTIONS,
  download,
  label,
  number,
  request,
  sourceUrl,
  type Filters,
  type Row,
  type Study,
  type Workspace,
} from "@/lib/dashboard";

const PAGES = [
  "Overview",
  "Content",
  "Comments",
  "Recommendations",
  "Data & methods",
] as const;
type Page = (typeof PAGES)[number];
const PAGE_ICONS = [SquaresFour, Play, ChatCircleText, Lightbulb, Database];
const DESCRIPTION: Record<Page, string> = {
  Overview:
    "Understand the sample. Compare what’s observed. Find your next research direction.",
  Content:
    "Look closer at the messages, formats, and publishing patterns behind the numbers.",
  Comments:
    "Explore the sampled public conversation, then review what the cue rules can assess.",
  Recommendations:
    "Turn supported comparisons into a testable next-post experiment.",
  "Data & methods":
    "Trace the sources, review labels, and take your research evidence with you.",
};

function Panel({
  title,
  note,
  action,
  children,
  className = "",
}: {
  title: string;
  note?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {note && <p>{note}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
function Notice({
  children,
  danger = false,
}: {
  children: ReactNode;
  danger?: boolean;
}) {
  return (
    <div className={`research-notice ${danger ? "danger" : ""}`}>
      <Info size={17} />
      <div>{children}</div>
    </div>
  );
}
function Table({
  rows,
  columns,
  limit,
}: {
  rows: Row[];
  columns?: string[];
  limit?: number;
}) {
  if (!rows.length)
    return (
      <p className="empty-copy">
        No matching observations. Try a wider sample.
      </p>
    );
  const keys = columns || Object.keys(rows[0]);
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {keys.map((k) => (
              <th key={k}>{label(k)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, limit || rows.length).map((row, i) => (
            <tr key={i}>
              {keys.map((k) => (
                <td key={k}>
                  {k === "source_url" && sourceUrl(row[k]) ? (
                    <a
                      href={sourceUrl(row[k])!}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Open video <ArrowSquareOut size={12} />
                    </a>
                  ) : typeof row[k] === "number" ? (
                    number(row[k], 2)
                  ) : row[k] === null ? (
                    <span className="unknown">Unknown</span>
                  ) : (
                    String(row[k])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function Stats({
  items,
}: {
  items: { label: string; value: string; hint: string }[];
}) {
  return (
    <div className="stats">
      {items.map((item, i) => (
        <div className="stat" key={item.label}>
          <span>{item.label}</span>
          <div>
            <strong>{item.value}</strong>
            <span className="stat-index">0{i + 1}</span>
          </div>
          <small>{item.hint}</small>
        </div>
      ))}
    </div>
  );
}
function BarChart({
  rows,
  name,
  value,
  suffix = "",
  count = "n",
}: {
  rows: Row[];
  name: string;
  value: string;
  suffix?: string;
  count?: string;
}) {
  const max = Math.max(...rows.map((row) => Number(row[value]) || 0), 1);
  if (!rows.length)
    return (
      <p className="empty-copy">No measured groups in the active sample.</p>
    );
  return (
    <div className="bars">
      {rows.map((row, i) => (
        <div className="bar-row" key={i}>
          <div className="bar-name">
            <span
              className={`brand-dot brand-${String(row[name]).toLowerCase()}`}
            />
            <strong>{String(row[name] ?? "Unknown")}</strong>
            <small>n={number(row[count], 0)}</small>
            <b>
              {number(row[value], 2)}
              {suffix}
            </b>
          </div>
          <div className="bar-track">
            <span
              style={{
                width: `${(Math.max(0, Number(row[value]) || 0) / max) * 100}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
function Tabs({
  options,
  value,
  onChange,
}: {
  options: string[];
  value: string;
  onChange: (s: string) => void;
}) {
  return (
    <div className="tabs" role="tablist">
      {options.map((option) => (
        <button
          key={option}
          role="tab"
          aria-selected={option === value}
          onClick={() => onChange(option)}
        >
          {option}
        </button>
      ))}
    </div>
  );
}
function Disclosure({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <details>
      <summary>
        {title}
        <ArrowDown size={14} />
      </summary>
      <div className="details-content">{children}</div>
    </details>
  );
}
function DistributionPlot({ rows, metric }: { rows: Row[]; metric: string }) {
  const groups = Array.from(new Set(rows.map((row) => String(row.brand))))
    .slice(0, 12)
    .map((brand) => ({
      brand,
      values: rows
        .filter((row) => row.brand === brand && typeof row[metric] === "number")
        .map((row) => Number(row[metric]))
        .filter(Number.isFinite)
        .sort((a, b) => a - b),
    }))
    .filter((group) => group.values.length);
  if (!groups.length)
    return (
      <p className="empty-copy">No measured distribution in this sample.</p>
    );
  const max = Math.max(...groups.flatMap((group) => group.values), 1),
    x = (value: number) => 90 + (value / max) * 440;
  const quantile = (values: number[], q: number) => {
    const index = (values.length - 1) * q,
      low = Math.floor(index);
    return (
      values[low] + (values[Math.ceil(index)] - values[low]) * (index - low)
    );
  };
  return (
    <div className="distribution-plot">
      <svg
        role="img"
        aria-label="Observed within-brand distributions, showing quartiles, median, and individual videos"
        viewBox={`0 0 560 ${groups.length * 57 + 40}`}
      >
        {groups.map(({ brand, values }, i) => {
          const y = i * 57 + 25,
            q1 = quantile(values, 0.25),
            q3 = quantile(values, 0.75),
            median = quantile(values, 0.5),
            iqr = q3 - q1,
            low = values.find((v) => v >= q1 - 1.5 * iqr)!,
            high = [...values].reverse().find((v) => v <= q3 + 1.5 * iqr)!;
          return (
            <g key={brand}>
              <text x="0" y={y + 4}>
                {brand}
              </text>
              <line x1={x(low)} x2={x(high)} y1={y} y2={y} stroke="#83ae8f" />
              <line
                x1={x(low)}
                x2={x(low)}
                y1={y - 9}
                y2={y + 9}
                stroke="#83ae8f"
              />
              <line
                x1={x(high)}
                x2={x(high)}
                y1={y - 9}
                y2={y + 9}
                stroke="#83ae8f"
              />
              <rect
                x={x(q1)}
                y={y - 13}
                width={Math.max(x(q3) - x(q1), 1)}
                height="26"
                fill="#e8f2e6"
                stroke="#83ae8f"
              />
              <line
                x1={x(median)}
                x2={x(median)}
                y1={y - 13}
                y2={y + 13}
                stroke="#047857"
                strokeWidth="2"
              />
              {values.map((value, j) => (
                <circle
                  key={j}
                  cx={x(value)}
                  cy={y + ((j % 3) - 1) * 5}
                  r="2.4"
                  fill="#047857"
                  opacity=".5"
                >
                  <title>
                    {brand}: {number(value, 3)}
                  </title>
                </circle>
              ))}
            </g>
          );
        })}
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
          <text
            key={fraction}
            x={x(max * fraction)}
            y={groups.length * 57 + 18}
            textAnchor="middle"
          >
            {number(max * fraction, 1)}
          </text>
        ))}
      </svg>
      <p className="muted">
        Boxes show the middle 50% and median; whiskers use 1.5× IQR, and dots
        represent measured videos. Up to 12 brands are shown.
      </p>
    </div>
  );
}
function TimingHeatmap({ rows, mode }: { rows: Row[]; mode: string }) {
  const activity = mode === "Publishing activity";
  const eligible = activity ? rows : rows.filter((row) => row.eligible);
  const field = activity ? "videos" : "median";
  const max = Math.max(...eligible.map((row) => Number(row[field]) || 0), 1);
  const hours = Array.from({ length: 24 }, (_, i) => i);
  return (
    <div className="heatmap-wrap">
      <div className="heatmap">
        <span />
        {hours.map((hour) => (
          <span key={hour}>
            {hour % 3 === 0 ? `${String(hour).padStart(2, "0")}:00` : ""}
          </span>
        ))}
        {[
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday",
          "Saturday",
          "Sunday",
        ].map((day) => (
          <div className="heatmap-row" key={day}>
            <strong>{day.slice(0, 3)}</strong>
            {hours.map((hour) => {
              const cell = eligible.find(
                  (row) => row.weekday === day && Number(row.hour) === hour,
                ),
                value = cell ? Number(cell[field]) : null;
              return (
                <div
                  className={`heatmap-cell ${cell ? "populated" : ""}`}
                  key={hour}
                  style={{
                    backgroundColor: cell
                      ? `rgba(4,120,87,${0.12 + ((Number(value) || 0) / max) * 0.48})`
                      : undefined,
                  }}
                  title={`${day}, ${String(hour).padStart(2, "0")}:00 Asia/Karachi · ${cell ? `${cell.videos} videos, n=${cell.n}, median=${number(cell.median, 2)}` : "no eligible observations"}`}
                >
                  {value === null ? "·" : number(value, activity ? 0 : 1)}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <p className="muted">
        Each cell is one publishing hour in Asia/Karachi. Color shows{" "}
        {activity ? "observed video counts" : "eligible observed medians"};
        unmeasured cells remain blank.
      </p>
    </div>
  );
}

export default function Dashboard() {
  const [page, setPage] = useState<Page>("Overview");
  const [study, setStudy] = useState<Study | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [filterDraft, setFilterDraft] = useState<Filters>(DEFAULT_FILTERS);
  const [filterOpen, setFilterOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [busy, setBusy] = useState("Loading the saved YouTube study…");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [dataTab, setDataTab] = useState("Study & quality");
  const [contentTab, setContentTab] = useState("Topics & language");
  const [commentTab, setCommentTab] = useState("Explore comments");
  const [search, setSearch] = useState("");
  const [commentLabel, setCommentLabel] = useState("all");
  const [inspected, setInspected] = useState<string | null>(null);
  const [topicField, setTopicField] = useState("category_suggested");
  const [tagMode, setTagMode] = useState("Usage");
  const [timingMode, setTimingMode] = useState("Publishing activity");
  const [brief, setBrief] = useState("");
  const [labels, setLabels] = useState<Row[]>([]);
  const [reviewer, setReviewer] = useState("");
  const [evaluation, setEvaluation] = useState<{
    n: number;
    macro_f1: number;
    coverage: number;
    confusion_matrix: Row[];
  } | null>(null);
  const [importCsv, setImportCsv] = useState("");
  const [importName, setImportName] = useState("");
  const [preview, setPreview] = useState<{
    rows: number;
    columns: string[];
    preview: Row[];
    mapping: Record<string, string | null>;
    fields: string[];
  } | null>(null);
  const [mapping, setMapping] = useState<Record<string, string | null>>({});
  const [importManifest, setImportManifest] = useState<Record<string, string>>({
    source_name: "",
    source_type: "unverified",
    status: "unverified",
    source_timezone: "unknown",
    geographic_relevance: "Unknown; no verified Pakistani audience geography",
    license_notes: "",
    notes: "",
  });
  const [apiKey, setApiKey] = useState("");
  const exportRef = useRef<HTMLButtonElement>(null);

  function accept(result: Study, replaceWorkspace = false) {
    setStudy(result);
    setFilters(result.filters);
    setFilterDraft(result.filters);
    setEvaluation(null);
    if (replaceWorkspace && result.workspace) {
      setWorkspace(result.workspace);
      setLabels(result.workspace.raw.map((row) => ({ ...row })));
    }
  }
  async function task(message: string, action: () => Promise<void>) {
    if (busy) return;
    setBusy(message);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy("");
    }
  }
  async function load() {
    setBusy("Loading the saved YouTube study…");
    setError("");
    try {
      accept(await request<Study>("study"), true);
      setNotice("Saved public YouTube snapshot loaded.");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "The saved study could not be loaded.",
      );
    } finally {
      setBusy("");
    }
  }
  useEffect(() => {
    void load();
  }, []); // The saved snapshot is fetched once per browser visit.
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setFilterOpen(false);
        setMenuOpen(false);
        setInspected(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  useEffect(() => {
    if (!filterOpen && !inspected) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    const focusables = () =>
      Array.from(
        dialog?.querySelectorAll<HTMLElement>(
          "button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled)",
        ) || [],
      );
    focusables()[0]?.focus();
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const elements = focusables(),
        first = elements[0],
        last = elements.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      previous?.focus();
    };
  }, [filterOpen, inspected]);
  const payload = { workspace, filters };
  const measure =
    study?.measures[filters.metric] || "Interactions / 1,000 views";
  const posts = study?.posts || [],
    comments = study?.comments || [];
  const table = (name: string) => study?.tables[name] || [];
  const supported =
    study?.recommendations.filter(
      (card) => card.confidence === "Exploratory; requires validation",
    ) || [];
  const matchingPosts = posts.filter((row) =>
    `${row.title} ${row.caption}`.toLowerCase().includes(search.toLowerCase()),
  );
  const matchingComments = comments.filter(
    (row) =>
      (commentLabel === "all" || row.sentiment_label === commentLabel) &&
      String(row.comment_text).toLowerCase().includes(search.toLowerCase()),
  );
  const selectedPost = posts.find((row) => row.post_id === inspected);
  const dates = posts
    .map((row) => String(row.source_date || ""))
    .filter(Boolean)
    .sort();
  const reviewedCount = comments.filter(
    (row) => row.sentiment_label !== "unassessed",
  ).length;
  function navigate(next: Page) {
    setPage(next);
    setMenuOpen(false);
    setSearch("");
    setError("");
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  function exportStudy(format: string) {
    void task("Preparing your research export…", () =>
      download({ ...payload, format, brief }),
    );
  }
  function openExport() {
    navigate("Data & methods");
    setDataTab("Export");
  }

  return (
    <div className="dashboard-app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      {menuOpen && (
        <button
          className="menu-scrim"
          aria-label="Close navigation"
          onClick={() => setMenuOpen(false)}
        />
      )}
      <aside
        className={`research-sidebar ${menuOpen ? "open" : ""}`}
        aria-label="Main navigation"
      >
        <button className="wordmark" onClick={() => navigate("Overview")}>
          <span className="wordmark-symbol">
            <Database size={23} weight="duotone" />
          </span>
          <span>
            Content Detective<small>PAKISTAN TELECOM CORPUS</small>
          </span>
        </button>
        <div className="workspace-identity">
          <span>PK</span>
          <div>
            <strong>YouTube research</strong>
            <small>Jazz · Zong · Ufone</small>
          </div>
          <ShieldCheck size={18} />
        </div>
        <p className="nav-label">RESEARCH WORKSPACE</p>
        <nav>
          {PAGES.map((name, i) => {
            const Icon = PAGE_ICONS[i];
            return (
              <button
                key={name}
                onClick={() => navigate(name)}
                aria-current={page === name ? "page" : undefined}
              >
                <Icon
                  size={19}
                  weight={page === name ? "duotone" : "regular"}
                />
                <span>{name}</span>
                {page === name && <span className="nav-active-dot" />}
              </button>
            );
          })}
        </nav>
        <button className="export-button" onClick={openExport}>
          <DownloadSimple size={18} />
          Export research
          <ArrowRight size={16} />
        </button>
        <div className="sidebar-bottom">
          <div className="corpus-status">
            <div>
              <span className="live-dot" />
              <strong>Saved research snapshot</strong>
            </div>
            <p>Public observations from official brand channels.</p>
            <small>
              {study?.manifest.collected_on
                ? new Date(study.manifest.collected_on).toLocaleDateString(
                    "en-GB",
                    {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                      timeZone: "Asia/Karachi",
                    },
                  )
                : "Loading snapshot"}
            </small>
          </div>
          <button
            className="guide-link"
            onClick={() => {
              navigate("Data & methods");
              setDataTab("Study & quality");
            }}
          >
            <BookOpen size={17} />
            Methods & source notes
            <ArrowSquareOut size={13} />
          </button>
          <div className="sidebar-footer">
            Pakistan-market content research
            <small>Observations, with context.</small>
          </div>
        </div>
      </aside>

      <div className="dashboard-body">
        <header className="masthead">
          <div>
            <button
              className="mobile-menu"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Open navigation"
            >
              <List size={22} />
            </button>
            <span>PakTelco Analytical Observational Workbench</span>
          </div>
          <div className="masthead-right">
            <span className="verified-label">
              <ShieldCheck size={15} />
              Official YouTube API sources
            </span>
            <span className="avatar">PK</span>
          </div>
        </header>
        <main id="main">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{page}</strong>
            <span className="scope-label">YOUTUBE ONLY</span>
          </div>
          <div className="page-heading">
            <div>
              <p className="eyebrow">
                <span />
                PAKISTAN TELECOM · CONTENT RESEARCH
              </p>
              <h1>{page}</h1>
              <p>{DESCRIPTION[page]}</p>
            </div>
            <button
              className="button secondary"
              onClick={() => {
                setFilterDraft(filters);
                setFilterOpen(true);
              }}
              disabled={!study || !!busy}
            >
              <Funnel size={17} />
              Filter sample<span className="button-count">{posts.length}</span>
            </button>
          </div>
          {error && (
            <div role="alert" className="error-alert">
              <Info size={18} />
              <span>{error}</span>
              <button onClick={() => setError("")} aria-label="Dismiss error">
                <X size={16} />
              </button>
            </div>
          )}
          {busy && (
            <div role="status" className="busy-alert">
              <SpinnerGap className="spin" size={18} />
              {busy}
            </div>
          )}
          {notice && !busy && (
            <div className="success-alert" role="status">
              <CheckCircle size={16} />
              <span>{notice}</span>
              <button
                onClick={() => setNotice("")}
                aria-label="Dismiss notification"
              >
                <X size={15} />
              </button>
            </div>
          )}
          {!study && !busy && (
            <Panel
              title="Research service unavailable"
              note="The interface is ready, but the saved study could not be loaded."
            >
              <button className="button primary" onClick={() => void load()}>
                <ArrowsClockwise size={16} />
                Retry loading study
              </button>
            </Panel>
          )}
          {study && (
            <>
              <div className="snapshot-banner">
                <div className="snapshot-icon">
                  <Database size={22} />
                </div>
                <div>
                  <strong>
                    {study.manifest.source_type === "official_api"
                      ? "Official API snapshot"
                      : study.data_label}
                  </strong>
                  <span>
                    {posts.length} videos <i>·</i> {comments.length} sampled
                    comments <i>·</i> {study.summary.brands}{" "}
                    {study.summary.brands === 1 ? "brand" : "brands"}
                  </span>
                </div>
                <span className="snapshot-right">
                  <span className="live-dot" />
                  Saved observations
                </span>
              </div>
              {study.mixed_tracks && (
                <Notice danger>
                  This workspace mixes data-status tracks. Keep synthetic,
                  declared-real, and unverified observations separate before
                  comparing groups or exporting findings.
                </Notice>
              )}
              {posts.length === 0 && page !== "Data & methods" ? (
                <Panel
                  title="No videos match this sample"
                  note="Select a brand or widen your date and video-age filters."
                >
                  <button
                    className="button secondary"
                    onClick={() => {
                      setFilterDraft(DEFAULT_FILTERS);
                      setFilterOpen(true);
                    }}
                  >
                    Adjust filters
                  </button>
                </Panel>
              ) : (
                <>
                  {page === "Overview" && (
                    <>
                      <div className="filter-ribbon">
                        <div>
                          <small>BRAND CORPUS FILTER</small>
                          <div className="brand-pills">
                            {filters.brands.map((brand) => (
                              <button
                                className={`brand-pill ${brand.toLowerCase()}`}
                                key={brand}
                                onClick={() =>
                                  void task(
                                    "Updating the research sample…",
                                    async () => {
                                      accept(
                                        await request<Study>("analyze", {
                                          workspace,
                                          filters: {
                                            ...filters,
                                            brands: filters.brands.filter(
                                              (b) => b !== brand,
                                            ),
                                          },
                                        }),
                                      );
                                    },
                                  )
                                }
                                disabled={!!busy}
                                aria-label={`Remove ${brand} from sample`}
                              >
                                {brand}
                                <X size={11} />
                              </button>
                            ))}
                          </div>
                        </div>
                        <div>
                          <small>OBSERVED MEASURE</small>
                          <strong className="measure-text">
                            <ChartLineUp size={16} />
                            {measure}
                          </strong>
                        </div>
                        <div>
                          <small>OBSERVED PUBLICATIONS</small>
                          <strong>
                            {dates.length
                              ? `${dates[0]} — ${dates.at(-1)}`
                              : "No known dates"}
                          </strong>
                        </div>
                      </div>
                      <Stats
                        items={[
                          {
                            label: "Videos in view",
                            value: number(posts.length, 0),
                            hint: "After active sample filters",
                          },
                          {
                            label: "Comments sampled",
                            value: number(comments.length, 0),
                            hint: "Linked public top-level comments",
                          },
                          {
                            label: "Brands",
                            value: number(study.summary.brands, 0),
                            hint: "Distinct observed brand channels",
                          },
                          {
                            label: "Measure coverage",
                            value: posts.length
                              ? `${Math.round((study.summary.valid_metric_posts / posts.length) * 100)}%`
                              : "N/A",
                            hint: "Videos with required counts",
                          },
                        ]}
                      />
                      <div className="overview-grid">
                        <Panel
                          title="Observed engagement by brand"
                          note={study.measure_notes[filters.metric]}
                          action={
                            <span className="tag">
                              MEDIAN · n ≥ {filters.minimum_group_n}
                            </span>
                          }
                        >
                          <BarChart
                            rows={table("brands")}
                            name="brand"
                            value="median"
                          />
                          <div className="chart-footnote">
                            Bars show observed medians. Account size, video age,
                            campaigns, and promotion may explain differences.
                          </div>
                          <Disclosure title="Compare distributions and video ages">
                            <DistributionPlot
                              rows={posts}
                              metric={filters.metric}
                            />
                            <Table
                              rows={table("brands")}
                              columns={[
                                "brand",
                                "total_posts",
                                "n",
                                "median",
                                "mean",
                                "youngest_days",
                                "oldest_days",
                                "coverage_pct",
                              ]}
                            />
                          </Disclosure>
                        </Panel>
                        <Panel
                          title="What this sample can answer"
                          note="Evidence against the seven research questions."
                          className="questions-panel"
                        >
                          {study.questions.map((row, i) => (
                            <div className="question-row" key={i}>
                              <span>0{i + 1}</span>
                              <div>
                                <strong>
                                  {
                                    [
                                      "Platform comparison",
                                      "Content formats",
                                      "Topics & hashtags",
                                      "Caption tone",
                                      "Posting day & time",
                                      "Audience demographics",
                                      "Next content experiment",
                                    ][i]
                                  }
                                </strong>
                                <small
                                  className={`support ${String(row.support).toLowerCase()}`}
                                >
                                  {i === 0 && study.summary.brands
                                    ? "YouTube only"
                                    : String(row.support)}
                                </small>
                              </div>
                            </div>
                          ))}
                        </Panel>
                      </div>
                      {study.summary.brands > 1 &&
                        !study.summary.age_comparability
                          .shared_age_range_exists && (
                          <Notice>
                            These brands do not share a known video-age range in
                            this sample. Brand comparisons remain descriptive.
                          </Notice>
                        )}
                      <div className="overview-grid bottom-grid">
                        <Panel
                          title="Your research, with substance"
                          note="Follow the observation from source to experiment."
                        >
                          <div className="workflow-links">
                            {[
                              {
                                title: "Inspect the content",
                                text: "Topics, language, hashtags & video sources",
                                page: "Content",
                              },
                              {
                                title: "Read the conversation",
                                text: "Public comment samples & label review",
                                page: "Comments",
                              },
                              {
                                title: "Design an experiment",
                                text: "Evidence-supported creative directions",
                                page: "Recommendations",
                              },
                            ].map((item) => (
                              <button
                                key={item.title}
                                onClick={() => navigate(item.page as Page)}
                              >
                                <span>
                                  <strong>{item.title}</strong>
                                  <small>{item.text}</small>
                                </span>
                                <ArrowRight size={18} />
                              </button>
                            ))}
                          </div>
                        </Panel>
                        <div className="limits-card">
                          <ShieldCheck size={25} />
                          <h2>Know what the data can say.</h2>
                          <p>
                            Missing shares, saves, reach, impressions, and
                            audience demographics stay unknown. Cue rules
                            require human review.
                          </p>
                          <button onClick={() => navigate("Data & methods")}>
                            Read the methods
                            <ArrowRight size={15} />
                          </button>
                        </div>
                      </div>
                    </>
                  )}

                  {page === "Content" && (
                    <>
                      <Tabs
                        options={[
                          "Topics & language",
                          "Hashtags",
                          "Posting patterns",
                          "Video library",
                        ]}
                        value={contentTab}
                        onChange={(value) => {
                          setContentTab(value);
                          setSearch("");
                        }}
                      />
                      {contentTab === "Topics & language" && (
                        <Panel
                          title="Content patterns in this sample"
                          note="Suggested category and language labels are unevaluated cues. Reviewed labels describe content, not viewer demographics."
                          action={
                            <button
                              className="text-button"
                              onClick={() => {
                                navigate("Data & methods");
                                setDataTab("Review labels");
                              }}
                            >
                              Review labels
                              <ArrowRight size={15} />
                            </button>
                          }
                        >
                          <div className="inline-controls">
                            <label>
                              Compare by
                              <select
                                value={topicField}
                                onChange={(e) => setTopicField(e.target.value)}
                              >
                                {Object.entries({
                                  category_suggested: "Suggested categories",
                                  language_inferred:
                                    "Suggested caption language",
                                  topic: "Reviewed topics",
                                  caption_language: "Reviewed caption language",
                                  creative_angle: "Creative approach",
                                  local_context: "Local context",
                                  content_type: "Media format",
                                  sentiment_label: "Caption tone",
                                }).map(([key, value]) => (
                                  <option key={key} value={key}>
                                    {value}
                                  </option>
                                ))}
                              </select>
                            </label>
                          </div>
                          <BarChart
                            rows={table(
                              (
                                {
                                  category_suggested: "suggested_categories",
                                  topic: "reviewed_topics",
                                } as Record<string, string>
                              )[topicField] || topicField,
                            )}
                            name={topicField}
                            value="median"
                          />
                          <Disclosure title="Group values and metric coverage">
                            <Table
                              rows={table(
                                (
                                  {
                                    category_suggested: "suggested_categories",
                                    topic: "reviewed_topics",
                                  } as Record<string, string>
                                )[topicField] || topicField,
                              )}
                            />
                          </Disclosure>
                        </Panel>
                      )}
                      {contentTab === "Hashtags" && (
                        <Panel
                          title="Hashtags used in these videos"
                          note="Frequency describes these sampled brand posts. It does not establish nationwide popularity or a hashtag’s causal effect."
                        >
                          <Tabs
                            options={["Usage", "Engagement association"]}
                            value={tagMode}
                            onChange={setTagMode}
                          />
                          <BarChart
                            rows={(tagMode === "Usage"
                              ? [...table("hashtags")].sort(
                                  (a, b) =>
                                    Number(b.total_posts) -
                                    Number(a.total_posts),
                                )
                              : table("hashtags").filter(
                                  (row) =>
                                    Number(row.n) >= filters.minimum_group_n &&
                                    Number(row.coverage_pct) >= 80,
                                )
                            ).slice(0, 12)}
                            name="hashtag"
                            value={
                              tagMode === "Usage" ? "total_posts" : "median"
                            }
                            count="total_posts"
                          />
                          <Disclosure title="Full hashtag evidence table">
                            <Table rows={table("hashtags")} />
                          </Disclosure>
                        </Panel>
                      )}
                      {contentTab === "Posting patterns" && (
                        <Panel
                          title="Publishing patterns"
                          note="Asia/Karachi time. Unknown timezones are excluded. Repeated observations are needed before proposing a posting window."
                        >
                          <Tabs
                            options={[
                              "Publishing activity",
                              "Observed engagement",
                            ]}
                            value={timingMode}
                            onChange={setTimingMode}
                          />
                          {timingMode === "Observed engagement" &&
                          !table("posting_cells").some(
                            (row) => row.eligible,
                          ) ? (
                            <Notice>
                              No day/hour slot has {filters.minimum_group_n}{" "}
                              measured videos with 80% metric coverage. Collect
                              repeated slots before recommending a time.
                            </Notice>
                          ) : (
                            <TimingHeatmap
                              rows={table("posting_cells")}
                              mode={timingMode}
                            />
                          )}
                          <Disclosure title="Exact day/hour observations">
                            <Table rows={table("posting_cells")} />
                          </Disclosure>
                        </Panel>
                      )}
                      {contentTab === "Video library" && (
                        <Panel
                          title="Source video library"
                          note="Inspect the actual post, observed counts, and label suggestions."
                        >
                          <Search
                            value={search}
                            onChange={setSearch}
                            placeholder="Search title or caption"
                          />
                          <p className="table-caption">
                            {matchingPosts.length} matching videos · select a
                            title to inspect
                          </p>
                          <div className="table-scroll">
                            <table>
                              <thead>
                                <tr>
                                  <th>Brand / title</th>
                                  <th>{measure}</th>
                                  <th>Age (days)</th>
                                  <th>Vs brand median</th>
                                  <th>Source</th>
                                </tr>
                              </thead>
                              <tbody>
                                {matchingPosts.map((row) => (
                                  <tr key={String(row.post_id)}>
                                    <td>
                                      <small className="table-brand">
                                        {String(row.brand)}
                                      </small>
                                      <button
                                        className="video-title"
                                        onClick={() =>
                                          setInspected(String(row.post_id))
                                        }
                                      >
                                        {String(row.title || row.post_id)}
                                      </button>
                                    </td>
                                    <td>{number(row[filters.metric], 2)}</td>
                                    <td>
                                      {number(row.age_days_at_snapshot, 0)}
                                    </td>
                                    <td>
                                      {number(row.brand_relative_index, 2)}
                                    </td>
                                    <td>
                                      {sourceUrl(row.source_url) && (
                                        <a
                                          href={sourceUrl(row.source_url)!}
                                          target="_blank"
                                          rel="noreferrer"
                                          aria-label={`Open source for ${row.title}`}
                                        >
                                          <ArrowSquareOut size={17} />
                                        </a>
                                      )}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          <p className="muted">
                            1.0 means the observed within-brand median. This
                            descriptive index is not a view forecast.
                          </p>
                        </Panel>
                      )}
                    </>
                  )}

                  {page === "Comments" && (
                    <>
                      <Stats
                        items={[
                          {
                            label: "Comments sampled",
                            value: number(comments.length, 0),
                            hint: "Recent top-level public comments",
                          },
                          {
                            label: "Cue labels assigned",
                            value: number(reviewedCount, 0),
                            hint: "Unevaluated language cue rules",
                          },
                          {
                            label: "Needs review",
                            value: number(comments.length - reviewedCount, 0),
                            hint: "Unassessed does not mean neutral",
                          },
                          {
                            label: "Rule coverage",
                            value: comments.length
                              ? `${((reviewedCount / comments.length) * 100).toFixed(1)}%`
                              : "N/A",
                            hint: "Label coverage, not accuracy",
                          },
                        ]}
                      />
                      <Tabs
                        options={["Explore comments", "Review & evaluate"]}
                        value={commentTab}
                        onChange={(value) => {
                          setCommentTab(value);
                          setSearch("");
                        }}
                      />
                      {commentTab === "Explore comments" ? (
                        <Panel
                          title="The sampled conversation"
                          note="English, Urdu, and Roman Urdu cue rules are unevaluated. This capped, self-selected sample is not representative audience sentiment."
                        >
                          <div className="comment-distribution">
                            {["Jazz", "Zong", "Ufone"]
                              .filter((brand) =>
                                comments.some((row) => row.brand === brand),
                              )
                              .map((brand) => {
                                const rows = comments.filter(
                                  (row) => row.brand === brand,
                                );
                                return (
                                  <div key={brand}>
                                    <strong>
                                      {brand}
                                      <small>{rows.length} sampled</small>
                                    </strong>
                                    <div className="stacked-track">
                                      {[
                                        "positive",
                                        "negative",
                                        "neutral",
                                        "unassessed",
                                      ].map((tone) => (
                                        <span
                                          key={tone}
                                          className={`tone-${tone}`}
                                          style={{
                                            width: `${(rows.filter((row) => row.sentiment_label === tone).length / rows.length) * 100}%`,
                                          }}
                                          title={`${tone}: ${rows.filter((row) => row.sentiment_label === tone).length}`}
                                        />
                                      ))}
                                    </div>
                                  </div>
                                );
                              })}
                          </div>
                          <div className="legend">
                            <span className="positive">Positive cue</span>
                            <span className="negative">Negative cue</span>
                            <span>Unassessed</span>
                          </div>
                          <div className="comment-controls">
                            <label>
                              Comment label
                              <select
                                value={commentLabel}
                                onChange={(e) =>
                                  setCommentLabel(e.target.value)
                                }
                              >
                                <option value="all">All comments</option>
                                <option value="unassessed">Needs review</option>
                                <option value="positive">Positive cue</option>
                                <option value="negative">Negative cue</option>
                                <option value="neutral">Neutral cue</option>
                              </select>
                            </label>
                            <Search
                              value={search}
                              onChange={setSearch}
                              placeholder="Search sampled comments"
                            />
                          </div>
                          <p className="table-caption">
                            {matchingComments.length} matching sampled comments
                            · preview limited to 40 rows
                          </p>
                          <Table
                            rows={matchingComments}
                            columns={[
                              "brand",
                              "comment_text",
                              "language_inferred",
                              "sentiment_label",
                            ]}
                            limit={40}
                          />
                          <p className="muted">
                            Total video comment metrics may include replies and
                            comments outside this sample. Author profile fields
                            were not collected.
                          </p>
                        </Panel>
                      ) : (
                        <Panel
                          title="Evaluate against human-reviewed labels"
                          note="Download the sheet, fill human_label with positive, neutral, or negative, then upload your reviewed CSV."
                        >
                          <div className="action-row">
                            <button
                              className="button secondary"
                              onClick={() => exportStudy("review")}
                              disabled={!!busy}
                            >
                              <DownloadSimple size={17} />
                              Download review sheet
                            </button>
                            <label className="button secondary upload-label">
                              <UploadSimple size={17} />
                              Upload reviewed labels
                              <input
                                type="file"
                                accept=".csv,text/csv"
                                disabled={!!busy}
                                onChange={(e) => {
                                  const file = e.target.files?.[0];
                                  if (file)
                                    void task(
                                      "Evaluating supplied human labels…",
                                      async () => {
                                        const result = await request<{
                                          evaluation: typeof evaluation;
                                        }>("evaluate", {
                                          ...payload,
                                          csv: await file.text(),
                                        });
                                        setEvaluation(result.evaluation);
                                        if (!result.evaluation)
                                          setNotice(
                                            "No nonblank human labels matched this sample.",
                                          );
                                      },
                                    );
                                  e.target.value = "";
                                }}
                              />
                            </label>
                          </div>
                          {evaluation ? (
                            <>
                              <Stats
                                items={[
                                  {
                                    label: "Reviewed sample",
                                    value: number(evaluation.n, 0),
                                    hint: "Matched nonblank human labels",
                                  },
                                  {
                                    label: "Macro-F1",
                                    value: number(evaluation.macro_f1, 3),
                                    hint: "Across positive, neutral, negative",
                                  },
                                  {
                                    label: "Rule coverage",
                                    value: `${(evaluation.coverage * 100).toFixed(1)}%`,
                                    hint: "Abstentions count as missed labels",
                                  },
                                ]}
                              />
                              <Table rows={evaluation.confusion_matrix} />
                            </>
                          ) : (
                            <Notice>
                              No evaluation score is available until reviewed
                              labels are supplied.
                            </Notice>
                          )}
                          <p className="muted">
                            Small or selectively reviewed samples limit
                            interpretation. Blank human labels never become
                            ground truth.
                          </p>
                        </Panel>
                      )}
                    </>
                  )}

                  {page === "Recommendations" && (
                    <>
                      <div className="recommendation-intro">
                        <span className="large-icon">
                          <Lightbulb size={27} weight="duotone" />
                        </span>
                        <div>
                          <h2>Evidence-supported content experiments</h2>
                          <p>
                            Source examples support a measured comparison.
                            Results still need validation.
                          </p>
                        </div>
                        <span className="tag">NO AI MODEL CALLS</span>
                      </div>
                      {supported.length ? (
                        supported.map((card) => (
                          <Panel
                            key={card.kind}
                            title={card.kind}
                            note={card.action}
                          >
                            <div className="action-row">
                              {card.examples?.map(
                                (example) =>
                                  sourceUrl(example.url) && (
                                    <a
                                      key={example.url}
                                      className="button secondary"
                                      href={sourceUrl(example.url)!}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      {example.group}: source example
                                      <ArrowSquareOut size={14} />
                                    </a>
                                  ),
                              )}
                            </div>
                            <Disclosure title="Supporting evidence and limitations">
                              <p>{card.evidence}</p>
                              <p className="muted">{card.limitations}</p>
                            </Disclosure>
                          </Panel>
                        ))
                      ) : (
                        <Notice>
                          No comparison currently clears the evidence threshold.
                          Review content labels or collect more comparable
                          observations before choosing a winner.
                        </Notice>
                      )}
                      <Panel
                        title="What needs more evidence"
                        note="The same sample-size and coverage guardrails apply to every proposed comparison."
                      >
                        {study.recommendations
                          .filter(
                            (card) =>
                              card.confidence === "Insufficient evidence",
                          )
                          .map((card) => (
                            <Disclosure title={card.kind} key={card.kind}>
                              <p>{card.action}</p>
                              <p className="muted">{card.evidence}</p>
                            </Disclosure>
                          ))}
                      </Panel>
                      <Panel
                        title="Prepare an AI-assisted writing brief"
                        note="Package computed evidence for a writing assistant. This creates a brief; it does not call an AI model."
                      >
                        <label>
                          Brand, objective, and creative constraints
                          <textarea
                            value={brief}
                            onChange={(e) => setBrief(e.target.value)}
                            placeholder="Describe the brand, product, objective, and constraints for the next post."
                            rows={4}
                          />
                        </label>
                        <button
                          className="button primary"
                          disabled={
                            !!busy || !brief.trim() || study.mixed_tracks
                          }
                          onClick={() => exportStudy("brief")}
                        >
                          <DownloadSimple size={17} />
                          Download evidence-based brief
                        </button>
                        <p className="muted">
                          Success measure: {measure}. Compare variants after
                          equal observation windows; keep the product, platform,
                          and paid exposure comparable.
                        </p>
                      </Panel>
                    </>
                  )}

                  {page === "Data & methods" && (
                    <>
                      <Tabs
                        options={[
                          "Study & quality",
                          "Review labels",
                          "Collect / import",
                          "Export",
                        ]}
                        value={dataTab}
                        onChange={setDataTab}
                      />
                      {dataTab === "Study & quality" && (
                        <>
                          <Panel
                            title="Current study"
                            note={study.manifest.source_name}
                          >
                            <p>{study.manifest.geographic_relevance}</p>
                            <span className="data-status-label">
                              {study.data_label}
                            </span>
                            <Table rows={table("source_coverage")} />
                            <Disclosure title="Source verification and sampling">
                              <p>{study.manifest.notes}</p>
                              <pre>
                                {JSON.stringify(study.verification, null, 2)}
                              </pre>
                            </Disclosure>
                            <Disclosure title="Metric formulas and coverage">
                              <Table rows={study.metric_coverage} />
                            </Disclosure>
                            <Disclosure title="Import quality and provenance">
                              <pre>
                                {JSON.stringify(
                                  {
                                    quality: study.quality,
                                    manifest: study.manifest,
                                  },
                                  null,
                                  2,
                                )}
                              </pre>
                            </Disclosure>
                          </Panel>
                          <Panel title="Interpretation limits">
                            <ul className="limits-list">
                              {study.summary.limitations.map((limit) => (
                                <li key={limit}>{limit}</li>
                              ))}
                              <li>
                                Public-comment cue labels and caption tone
                                describe separate texts.
                              </li>
                              <li>
                                Raw lineage paths identify the acquisition
                                receipts; the hosted snapshot does not bundle
                                the raw API responses.
                              </li>
                            </ul>
                            <a
                              className="text-button"
                              href="https://github.com/adnanf787/content-detective/blob/main/docs/FEATURE_GUIDE.md"
                              target="_blank"
                              rel="noreferrer"
                            >
                              Read the full feature guide
                              <ArrowSquareOut size={15} />
                            </a>
                          </Panel>
                        </>
                      )}
                      {dataTab === "Review labels" && (
                        <Panel
                          title="Review content labels"
                          note="Edit labels for the entire loaded dataset. Source text and measured counts stay preserved. Save with a reviewer and codebook note."
                        >
                          <div className="label-editor">
                            <table>
                              <thead>
                                <tr>
                                  <th>Brand / title</th>
                                  {LABEL_FIELDS.map((field) => (
                                    <th key={field}>{label(field)}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {labels.map((row, i) => (
                                  <tr key={i}>
                                    <td>
                                      <small className="table-brand">
                                        {String(row.brand)}
                                      </small>
                                      <strong>
                                        {String(
                                          row.title ||
                                            row.caption ||
                                            row.post_id,
                                        ).slice(0, 90)}
                                      </strong>
                                      {sourceUrl(row.source_url) && (
                                        <a
                                          href={sourceUrl(row.source_url)!}
                                          target="_blank"
                                          rel="noreferrer"
                                        >
                                          Source
                                          <ArrowSquareOut size={11} />
                                        </a>
                                      )}
                                    </td>
                                    {LABEL_FIELDS.map((field) => (
                                      <td key={field}>
                                        {LABEL_OPTIONS[field] ? (
                                          <select
                                            aria-label={`${label(field)} for video ${i + 1}`}
                                            value={String(row[field] || "")}
                                            onChange={(e) =>
                                              setLabels((previous) =>
                                                previous.map((r, index) =>
                                                  index === i
                                                    ? {
                                                        ...r,
                                                        [field]: e.target.value,
                                                      }
                                                    : r,
                                                ),
                                              )
                                            }
                                          >
                                            {Array.from(
                                              new Set([
                                                ...LABEL_OPTIONS[field],
                                                String(row[field] || ""),
                                              ]),
                                            ).map((option) => (
                                              <option
                                                key={option}
                                                value={option}
                                              >
                                                {option || "Unknown"}
                                              </option>
                                            ))}
                                          </select>
                                        ) : (
                                          <input
                                            aria-label={`${label(field)} for video ${i + 1}`}
                                            value={String(row[field] || "")}
                                            onChange={(e) =>
                                              setLabels((previous) =>
                                                previous.map((r, index) =>
                                                  index === i
                                                    ? {
                                                        ...r,
                                                        [field]: e.target.value,
                                                      }
                                                    : r,
                                                ),
                                              )
                                            }
                                          />
                                        )}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          <label>
                            Reviewer / codebook / annotation method
                            <input
                              value={reviewer}
                              onChange={(e) => setReviewer(e.target.value)}
                              placeholder="Reviewed by Ayesha; codebook v1"
                            />
                          </label>
                          <button
                            className="button primary"
                            disabled={!!busy || !reviewer.trim()}
                            onClick={() =>
                              void task(
                                "Saving reviewed labels and recalculating…",
                                async () => {
                                  accept(
                                    await request<Study>("labels", {
                                      ...payload,
                                      labels,
                                      reviewer,
                                    }),
                                    true,
                                  );
                                  setNotice(
                                    "Labels applied to this workspace. Export the analyzed rows to retain your review.",
                                  );
                                },
                              )
                            }
                          >
                            <CheckCircle size={17} />
                            Save reviewed labels and recalculate
                          </button>
                          <p className="muted">
                            Changes stay in this browser visit. Export before
                            reloading. Video length alone does not establish a
                            YouTube Short.
                          </p>
                        </Panel>
                      )}
                      {dataTab === "Collect / import" && (
                        <>
                          <Panel
                            title="Saved YouTube study"
                            note="Reload the validated public pilot without API calls. This replaces your active workspace."
                          >
                            <button
                              className="button secondary"
                              disabled={!!busy}
                              onClick={() => void load()}
                            >
                              <ArrowsClockwise size={16} />
                              Reload saved YouTube dataset
                            </button>
                          </Panel>
                          <Panel
                            title="Refresh the official telecom pilot"
                            note={`${String(study.collection_config.publication_start)} to ${String(study.collection_config.publication_end)} · ${String(study.collection_config.videos_per_brand)} videos per brand · up to ${String(study.collection_config.comments_per_video)} top-level comments per video.`}
                          >
                            <p>
                              A fresh collection sends requests to Google’s
                              official YouTube API using your own key. Your key
                              passes through this app to Google and is not
                              saved. The resulting workspace is temporary;
                              export it before closing.
                            </p>
                            <label>
                              Your YouTube Data API key
                              <input
                                type="password"
                                autoComplete="off"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Enter your own key to enable collection"
                              />
                            </label>
                            <button
                              className="button secondary"
                              disabled={!!busy || !apiKey.trim()}
                              onClick={() =>
                                void task(
                                  "Collecting official metadata and public comments. This may take a few minutes…",
                                  async () => {
                                    const key = apiKey;
                                    setApiKey("");
                                    const result = await request<Study>(
                                      "collect",
                                      { api_key: key },
                                    );
                                    accept(result, true);
                                    setNotice(
                                      `Fresh snapshot loaded: ${result.posts.length} videos and ${result.comments.length} sampled comments. Export your results before closing.`,
                                    );
                                  },
                                )
                              }
                            >
                              <GlobeHemisphereEast size={17} />
                              Collect a fresh YouTube snapshot
                            </button>
                            <p className="muted">
                              Collection uses your API quota. An unavailable
                              source remains unavailable; the app does not
                              invent missing records.
                            </p>
                          </Panel>
                          <Panel
                            title="Import documented post observations"
                            note="Import a UTF-8 post-level CSV, review its column mapping, and declare provenance. The hosted request limit is 3.5 MB and 5,000 posts."
                          >
                            <div className="action-row">
                              <a
                                className="button secondary"
                                href="/api/template"
                                download
                              >
                                <DownloadSimple size={17} />
                                Download collection template
                              </a>
                            </div>
                            <label className="button secondary upload-label">
                              <UploadSimple size={17} />
                              Choose post CSV
                              <input
                                type="file"
                                accept=".csv,text/csv"
                                disabled={!!busy}
                                onChange={(e) => {
                                  const file = e.target.files?.[0];
                                  if (file)
                                    void task(
                                      "Reading the CSV preview…",
                                      async () => {
                                        if (file.size > 2_500_000)
                                          throw new Error(
                                            "Choose a CSV smaller than 2.5 MB for hosted import.",
                                          );
                                        const csv = await file.text();
                                        const result = await request<
                                          NonNullable<typeof preview>
                                        >("import/preview", { csv });
                                        setImportCsv(csv);
                                        setImportName(file.name);
                                        setPreview(result);
                                        setMapping(result.mapping);
                                      },
                                    );
                                  e.target.value = "";
                                }}
                              />
                            </label>
                            {preview && (
                              <>
                                <p className="table-caption">
                                  {importName} · {preview.rows} source rows ·{" "}
                                  {preview.columns.length} columns
                                </p>
                                <Table rows={preview.preview} />
                                <Disclosure title="Review column mapping">
                                  <div className="mapping-grid">
                                    {preview.fields.map((field) => (
                                      <label key={field}>
                                        {label(field)}
                                        <select
                                          value={mapping[field] || ""}
                                          onChange={(e) =>
                                            setMapping({
                                              ...mapping,
                                              [field]: e.target.value || null,
                                            })
                                          }
                                        >
                                          <option value="">Not provided</option>
                                          {preview.columns.map((column) => (
                                            <option key={column}>
                                              {column}
                                            </option>
                                          ))}
                                        </select>
                                      </label>
                                    ))}
                                  </div>
                                </Disclosure>
                                <div className="form-grid">
                                  <label>
                                    Source / publisher
                                    <input
                                      value={importManifest.source_name}
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          source_name: e.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                  <label>
                                    Dataset status
                                    <select
                                      value={importManifest.status}
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          status: e.target.value,
                                        })
                                      }
                                    >
                                      <option>unverified</option>
                                      <option>real</option>
                                      <option>synthetic</option>
                                    </select>
                                  </label>
                                  <label>
                                    Collection method
                                    <select
                                      value={importManifest.source_type}
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          source_type: e.target.value,
                                        })
                                      }
                                    >
                                      {[
                                        "unverified",
                                        "official_export",
                                        "manual_public_post",
                                        "third_party",
                                        "synthetic",
                                      ].map((value) => (
                                        <option key={value}>{value}</option>
                                      ))}
                                    </select>
                                  </label>
                                  <label>
                                    Source timezone
                                    <input
                                      value={importManifest.source_timezone}
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          source_timezone: e.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                  <label>
                                    Geographic relevance
                                    <input
                                      value={
                                        importManifest.geographic_relevance
                                      }
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          geographic_relevance: e.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                  <label>
                                    Collection date
                                    <input
                                      type="date"
                                      value={importManifest.collected_on || ""}
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          collected_on: e.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                  <label>
                                    Verified audience segment evidence
                                    <input
                                      value={
                                        importManifest.audience_evidence || ""
                                      }
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          audience_evidence: e.target.value,
                                        })
                                      }
                                      placeholder="Leave blank unless documented"
                                    />
                                  </label>
                                  <label>
                                    Permission / terms / license notes
                                    <input
                                      value={importManifest.license_notes}
                                      onChange={(e) =>
                                        setImportManifest({
                                          ...importManifest,
                                          license_notes: e.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                </div>
                                <label>
                                  Source and method notes
                                  <textarea
                                    value={importManifest.notes}
                                    onChange={(e) =>
                                      setImportManifest({
                                        ...importManifest,
                                        notes: e.target.value,
                                      })
                                    }
                                  />
                                </label>
                                <button
                                  className="button primary"
                                  disabled={
                                    !!busy || !importManifest.source_name.trim()
                                  }
                                  onClick={() =>
                                    void task(
                                      "Validating and activating the imported dataset…",
                                      async () => {
                                        accept(
                                          await request<Study>("import", {
                                            csv: importCsv,
                                            mapping,
                                            manifest: {
                                              ...importManifest,
                                              file_name: importName,
                                            },
                                          }),
                                          true,
                                        );
                                        setNotice(
                                          "Imported workspace activated. Unknown counts remain missing; real status is your declaration.",
                                        );
                                        setPreview(null);
                                        setDataTab("Study & quality");
                                      },
                                    )
                                  }
                                >
                                  <FileCsv size={17} />
                                  Validate and activate dataset
                                </button>
                              </>
                            )}
                          </Panel>
                        </>
                      )}
                      {dataTab === "Export" && (
                        <Panel
                          title="Export the active research sample"
                          note="Every export uses the active brand, publication-date, video-age, and measure filters. Comments are linked only to the selected videos."
                        >
                          <div className="export-summary">
                            <Database size={24} />
                            <div>
                              <strong>
                                {posts.length} videos · {comments.length}{" "}
                                sampled comments
                              </strong>
                              <p>
                                {measure} ·{" "}
                                {filters.brands.join(", ") ||
                                  "No brands selected"}
                              </p>
                            </div>
                          </div>
                          <div className="export-options">
                            {[
                              {
                                format: "zip",
                                name: "Research evidence ZIP",
                                text: "Findings, analyzed rows, linked comments, tables, filters, manifest, and quality checks.",
                              },
                              {
                                format: "report",
                                name: "Findings report",
                                text: "Computed Markdown report with source examples and interpretation limits.",
                              },
                              {
                                format: "posts",
                                name: "Analyzed videos",
                                text: "CSV including observed counts, content labels, and within-brand descriptive index.",
                              },
                              {
                                format: "comments",
                                name: "Sampled comments",
                                text: "CSV of public top-level comments linked to the current filtered sample.",
                              },
                              {
                                format: "summary",
                                name: "Analysis summary",
                                text: "JSON with definitions, counts, question support, and comparison guardrails.",
                              },
                            ].map((option, i) => (
                              <div key={option.format}>
                                <span className="export-file-icon">
                                  {option.format === "zip" ? (
                                    <Database size={21} />
                                  ) : (
                                    <FileCsv size={21} />
                                  )}
                                </span>
                                <div>
                                  <h3>{option.name}</h3>
                                  <p>{option.text}</p>
                                </div>
                                <button
                                  ref={i === 0 ? exportRef : undefined}
                                  className={`button ${i === 0 ? "primary" : "secondary"}`}
                                  aria-label={`Download ${option.name}`}
                                  onClick={() => exportStudy(option.format)}
                                  disabled={
                                    !!busy ||
                                    !posts.length ||
                                    study.mixed_tracks
                                  }
                                >
                                  <DownloadSimple size={17} />
                                  <span>Download</span>
                                </button>
                              </div>
                            ))}
                          </div>
                          <Notice>
                            Exports describe this observed sample. They do not
                            claim demographic response, causal posting effects,
                            or predicted view gains.
                          </Notice>
                        </Panel>
                      )}
                    </>
                  )}
                </>
              )}
            </>
          )}
          <footer className="research-footer">
            <span>
              Content Detective <i>·</i> Pakistan telecom research
            </span>
            <span>Real sources. Explicit limits.</span>
          </footer>
        </main>
      </div>

      {filterOpen && (
        <div className="modal-overlay" onClick={() => setFilterOpen(false)}>
          <section
            className="filter-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="filter-title"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="modal-close"
              aria-label="Close sample filters"
              onClick={() => setFilterOpen(false)}
            >
              <X size={20} />
            </button>
            <span className="large-icon">
              <Funnel size={25} />
            </span>
            <h2 id="filter-title">Filter your research sample</h2>
            <p>Filters apply across analysis and evidence exports.</p>
            <fieldset>
              <legend>Brands</legend>
              <div className="brand-checkboxes">
                {study?.available_brands.map((brand) => (
                  <label key={brand}>
                    <input
                      type="checkbox"
                      checked={filterDraft.brands.includes(brand)}
                      onChange={(e) =>
                        setFilterDraft({
                          ...filterDraft,
                          brands: e.target.checked
                            ? [...filterDraft.brands, brand]
                            : filterDraft.brands.filter((b) => b !== brand),
                        })
                      }
                    />
                    {brand}
                  </label>
                ))}
              </div>
            </fieldset>
            <label>
              Measure
              <select
                value={filterDraft.metric}
                onChange={(e) =>
                  setFilterDraft({ ...filterDraft, metric: e.target.value })
                }
              >
                {Object.entries(study?.measures || {}).map(([key, value]) => (
                  <option key={key} value={key}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-grid">
              <label>
                Publication start
                <input
                  type="date"
                  value={filterDraft.publication_start || ""}
                  onChange={(e) =>
                    setFilterDraft({
                      ...filterDraft,
                      publication_start: e.target.value,
                    })
                  }
                />
              </label>
              <label>
                Publication end
                <input
                  type="date"
                  value={filterDraft.publication_end || ""}
                  onChange={(e) =>
                    setFilterDraft({
                      ...filterDraft,
                      publication_end: e.target.value,
                    })
                  }
                />
              </label>
              <label>
                Minimum video age (days)
                <input
                  type="number"
                  min="0"
                  value={filterDraft.min_age_days ?? ""}
                  onChange={(e) =>
                    setFilterDraft({
                      ...filterDraft,
                      min_age_days:
                        e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                />
              </label>
              <label>
                Maximum video age (days)
                <input
                  type="number"
                  min="0"
                  value={filterDraft.max_age_days ?? ""}
                  onChange={(e) =>
                    setFilterDraft({
                      ...filterDraft,
                      max_age_days:
                        e.target.value === "" ? null : Number(e.target.value),
                    })
                  }
                />
              </label>
            </div>
            <label>
              Minimum videos per comparison group
              <input
                type="number"
                min="2"
                max="100"
                value={filterDraft.minimum_group_n}
                onChange={(e) =>
                  setFilterDraft({
                    ...filterDraft,
                    minimum_group_n: Number(e.target.value),
                  })
                }
              />
            </label>
            <p className="muted">
              Video age is measured at the collection snapshot. Unknown ages are
              excluded when an age filter is active.
            </p>
            <div className="action-row">
              <button
                className="button secondary"
                onClick={() =>
                  setFilterDraft({
                    ...DEFAULT_FILTERS,
                    brands: study?.available_brands || [],
                  })
                }
              >
                Reset filters
              </button>
              <button
                className="button primary"
                disabled={!!busy}
                onClick={() => {
                  setFilterOpen(false);
                  void task("Applying research filters…", async () =>
                    accept(
                      await request<Study>("analyze", {
                        workspace,
                        filters: filterDraft,
                      }),
                    ),
                  );
                }}
              >
                <CheckCircle size={17} />
                Apply filters
              </button>
            </div>
          </section>
        </div>
      )}
      {selectedPost && (
        <div className="modal-overlay" onClick={() => setInspected(null)}>
          <section
            className="video-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="video-title"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="modal-close"
              onClick={() => setInspected(null)}
              aria-label="Close video details"
            >
              <X size={20} />
            </button>
            <p className="eyebrow">
              {String(selectedPost.brand)} · SOURCE OBSERVATION
            </p>
            <h2 id="video-title">
              {String(selectedPost.title || selectedPost.post_id)}
            </h2>
            <p className="muted">
              Published {String(selectedPost.post_datetime)} · Age at snapshot:{" "}
              {number(selectedPost.age_days_at_snapshot, 0)} days
            </p>
            <p className="video-caption" dir="auto">
              {String(selectedPost.caption || "No caption available.")}
            </p>
            <Table
              rows={[
                "likes",
                "comments",
                "views",
                "language_inferred",
                "category_suggested",
                "category_evidence",
                "comment_sample_status",
                "downloaded_comment_count",
              ].map((field) => ({
                field: label(field),
                value: selectedPost[field],
              }))}
            />
            {sourceUrl(selectedPost.source_url) && (
              <a
                className="button primary"
                href={sourceUrl(selectedPost.source_url)!}
                target="_blank"
                rel="noreferrer"
              >
                Open original video
                <ArrowSquareOut size={16} />
              </a>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function Search({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="search-field">
      <span className="visually-hidden">{placeholder}</span>
      <MagnifyingGlass size={18} />
      <input
        aria-label={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      {value && (
        <button aria-label="Clear search" onClick={() => onChange("")}>
          <X size={14} />
        </button>
      )}
    </label>
  );
}
