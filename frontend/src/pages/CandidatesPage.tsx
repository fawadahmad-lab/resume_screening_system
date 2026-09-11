import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listScreenings } from "../api/screening";
import { CandidatesTable } from "../components/candidates/CandidatesTable";
import { LatestScreening } from "../components/candidates/LatestScreening";
import { SampleDataCard } from "../components/candidates/SampleDataCard";
import { Card } from "../components/ui/Card";
import { ErrorState, Spinner } from "../components/ui/States";
import { useScreeningPolling } from "../hooks/useScreeningPolling";

export function CandidatesPage() {
  const list = useQuery({
    queryKey: ["screenings"],
    queryFn: listScreenings,
  });

  const latestId = list.data?.screenings[0]?.id ?? null;
  const latest = useScreeningPolling(latestId);

  if (list.isLoading) {
    return <Spinner label="Loading screenings…" />;
  }
  if (list.isError) {
    return (
      <ErrorState
        message={list.error.message}
        onRetry={() => list.refetch()}
      />
    );
  }

  const hasRuns = (list.data?.screenings.length ?? 0) > 0;

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">Candidates</h1>
        <p className="page-subtitle">
          Ranked, evidence-backed fit assessments for your latest screening run.
        </p>
      </div>

      {latest.isLoading && hasRuns ? (
        <Spinner label="Loading latest screening…" />
      ) : latest.isError ? (
        <ErrorState
          message={latest.error.message}
          onRetry={() => latest.refetch()}
        />
      ) : latest.data ? (
        <>
          <LatestScreening run={latest.data} />
          <Card
            title="Ranked results"
            actions={
              <Link className="btn btn--ghost" to="/screening">
                New screening
              </Link>
            }
          >
            <CandidatesTable run={latest.data} />
          </Card>
        </>
      ) : (
        <Card>
          <div className="empty-state">
            <p style={{ fontWeight: 600 }}>No screenings yet</p>
            <p className="muted">
              Run your first screening to see ranked candidates here.
            </p>
            <Link
              className="btn btn--primary"
              to="/screening"
              style={{ marginTop: "var(--sp-4)" }}
            >
              Start a screening
            </Link>
          </div>
        </Card>
      )}

      <SampleDataCard />
    </div>
  );
}