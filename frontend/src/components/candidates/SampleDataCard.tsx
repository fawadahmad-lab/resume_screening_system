import { Link } from "react-router-dom";
import { Database } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { listJobs } from "../../api/jobs";
import { listSampleResumes } from "../../api/evals";
import { Card } from "../ui/Card";

export function SampleDataCard() {
  const resumes = useQuery({
    queryKey: ["sample-resumes"],
    queryFn: listSampleResumes,
  });
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: listJobs });

  const resumeCount = resumes.data?.resumes.length ?? 0;
  const jobCount = jobs.data?.jobs.length ?? 0;

  return (
    <Card
      title={
        <span className="row" style={{ gap: "var(--sp-2)" }}>
          <Database size={16} aria-hidden="true" />
          Sample / Demo Data
        </span>
      }
    >
      <div className="stack stack--sm">
        <p className="muted" style={{ fontSize: "var(--fs-sm)" }}>
          <span className="badge badge--sample" style={{ marginRight: "var(--sp-2)" }}>
            Sample
          </span>
          These are the repo&apos;s bundled synthetic resumes and job
          descriptions ({resumeCount} resumes, {jobCount} JDs). Use them in a
          screening to try the system without uploading files.
        </p>
        <div className="row">
          <Link className="btn btn--secondary" to="/screening">
            Screen sample candidates
          </Link>
          <Link className="btn btn--ghost" to="/evaluations">
            View dev-set evaluations
          </Link>
        </div>
      </div>
    </Card>
  );
}