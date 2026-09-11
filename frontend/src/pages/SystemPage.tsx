import { useQuery } from "@tanstack/react-query";
import { getSystemState } from "../api/system";
import { Card } from "../components/ui/Card";
import { ErrorState, Spinner } from "../components/ui/States";

const PROVIDER_LABEL: Record<string, string> = {
  groq: "Groq (OpenAI-compatible endpoint)",
  ollama: "Ollama (hosted, gpt-oss:120b)",
  auto: "Auto — Groq with on-detection failover to Ollama",
};

export function SystemPage() {
  const system = useQuery({ queryKey: ["system"], queryFn: getSystemState });

  if (system.isLoading) return <Spinner label="Loading system state…" />;
  if (system.isError) {
    return <ErrorState message={system.error.message} onRetry={() => system.refetch()} />;
  }
  const s = system.data;
  if (!s) {
    return <ErrorState message="No system state available." />;
  }
  const rows: [string, string][] = [
    ["Provider", PROVIDER_LABEL[s.provider] ?? s.provider],
    ["Scoring model", s.model],
    ["Structured output", "JSON schema, strict mode"],
    ["Temperature", String(s.temperature)],
    ["Max validation retries", String(s.max_retries)],
    ["Call pacing", `${s.call_interval_s}s between calls`],
    ["Request timeout", `${s.timeout_s}s`],
    ["Scoring ensemble", `n=${s.score_ensemble_n} (majority-vote on fit)`],
    ["Runtime data", s.data_dir],
  ];

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">System</h1>
        <p className="page-subtitle">
          Read-only view of the live scoring configuration as reported by the
          backend. Nothing here can be edited from this screen.
        </p>
      </div>

      <Card>
        <dl className="stack stack--sm">
          {rows.map(([k, v]) => (
            <div
              key={k}
              className="row"
              style={{ justifyContent: "space-between", gap: "var(--sp-5)" }}
            >
              <dt className="muted" style={{ flex: "0 0 13rem" }}>
                {k}
              </dt>
              <dd className="mono" style={{ textAlign: "right" }}>
                {v}
              </dd>
            </div>
          ))}
        </dl>
      </Card>
    </div>
  );
}