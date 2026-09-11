import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createScreening } from "../api/screening";
import { getJob, listJobs } from "../api/jobs";
import { listSampleResumes } from "../api/evals";
import { JdInput, type JdMode } from "../components/screening/JdInput";
import { ResumeInput } from "../components/screening/ResumeInput";
import { ScreeningProgress } from "../components/screening/ScreeningProgress";
import { ScreeningResults } from "../components/screening/ScreeningResults";
import { FailuresPanel } from "../components/screening/FailuresPanel";
import { Card } from "../components/ui/Card";
import { ErrorState } from "../components/ui/States";
import { useScreeningPolling, isRunning } from "../hooks/useScreeningPolling";

export function ScreeningPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [refreshedList, setRefreshedList] = useState(false);

  const sampleJobs = useQuery({ queryKey: ["jobs"], queryFn: listJobs });
  const sampleResumes = useQuery({
    queryKey: ["sample-resumes"],
    queryFn: listSampleResumes,
  });

  // JD state
  const [jdMode, setJdMode] = useState<JdMode>("paste");
  const [jdPasted, setJdPasted] = useState("");
  const [selectedSampleJob, setSelectedSampleJob] = useState<string | null>(null);
  const [sampleText, setSampleText] = useState<string>("");
  const [loadingSample, setLoadingSample] = useState(false);
  const [jdFile, setJdFile] = useState<File | null>(null);

  // Resume state
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [selectedSampleResumes, setSelectedSampleResumes] = useState<string[]>([]);

  // Submit / run state
  const [createdId, setCreatedId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const run = useScreeningPolling(createdId);

  // Load selected sample JD text
  useEffect(() => {
    if (!selectedSampleJob) {
      setSampleText("");
      return;
    }
    setLoadingSample(true);
    getJob(selectedSampleJob)
      .then((d) => setSampleText(d.text))
      .catch((e) => setSampleText(`Failed to load: ${e.message}`))
      .finally(() => setLoadingSample(false));
  }, [selectedSampleJob]);

  // Refresh the screenings list once a run reaches a terminal state so the
  // Candidates landing page reflects the new run.
  useEffect(() => {
    if (createdId && run.data?.status === "completed" && !refreshedList) {
      setRefreshedList(true);
      queryClient.invalidateQueries({ queryKey: ["screenings"] });
    }
    if (createdId && run.data?.status === "failed" && !refreshedList) {
      setRefreshedList(true);
    }
  }, [createdId, run.data?.status, refreshedList, queryClient]);

  const resolveJdText = (): string | null => {
    if (jdMode === "paste") return jdPasted.trim() || null;
    if (jdMode === "sample") return selectedSampleJob ? sampleText.trim() || null : null;
    if (jdMode === "upload") return jdFile ? null : null; // file posted separately
    return null;
  };

  const canSubmit =
    !submitting &&
    !run.data &&
    (uploadedFiles.length > 0 || selectedSampleResumes.length > 0) &&
    (jdMode === "upload"
      ? Boolean(jdFile)
      : jdMode === "sample"
        ? Boolean(selectedSampleJob && sampleText.trim())
        : resolveJdText() !== null);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setSubmitError(null);
    const form = new FormData();
    const text = resolveJdText();
    if (text) {
      form.append("jd_text", text);
    }
    if (jdMode === "sample" && selectedSampleJob) {
      form.append("jd_name", `Sample JD · ${selectedSampleJob}`);
    } else if (jdMode === "paste") {
      form.append("jd_name", "Pasted job description");
    } else if (jdMode === "upload" && jdFile) {
      form.append("jd_file", jdFile, jdFile.name);
    }
    uploadedFiles.forEach((f) => form.append("resumes", f));
    selectedSampleResumes.forEach((name) => form.append("sample_resumes", name));
    try {
      const res = await createScreening(form);
      setCreatedId(res.screening_id);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRunNew = () => {
    setCreatedId(null);
    setUploadedFiles([]);
    setSelectedSampleResumes([]);
    setJdPasted("");
    setSelectedSampleJob(null);
    setJdMode("paste");
    setJdFile(null);
    setRefreshedList(false);
  };

  if (run.data && isRunning(run.data.status)) {
    return (
      <div className="stack">
        <h1 className="page-title">Screening in progress</h1>
        <Card title={`Run ${run.data.id}`}>
          <ScreeningProgress run={run.data} />
        </Card>
      </div>
    );
  }

  if (run.data && run.data.status === "failed") {
    return (
      <div className="stack">
        <h1 className="page-title">Screening failed</h1>
        <Card>
          <div className="alert-banner alert-banner--danger" role="alert">
            {run.data.error ?? "The screening run failed at the batch level."}
          </div>
          <div className="row" style={{ marginTop: "var(--sp-4)" }}>
            <button className="btn btn--primary" onClick={handleRunNew}>
              Start another screening
            </button>
            <button className="btn btn--secondary" onClick={() => navigate("/")}>
              Back to candidates
            </button>
          </div>
        </Card>
      </div>
    );
  }

  if (run.data && run.data.status === "completed") {
    return (
      <div className="stack">
        <div className="spread">
          <div>
            <h1 className="page-title">Screening complete</h1>
            <p className="page-subtitle">
              Run <span className="mono">{run.data.id}</span> · {run.data.jd_name}
            </p>
          </div>
          <button className="btn btn--secondary" onClick={handleRunNew}>
            New screening
          </button>
        </div>
        <Card title="Results">
          <ScreeningResults run={run.data} />
        </Card>
        <FailuresPanel failures={run.data.failures} />
      </div>
    );
  }

  return (
    <div className="stack">
      <div>
        <h1 className="page-title">New Screening</h1>
        <p className="page-subtitle">
          Pick a job description and a batch of resumes, then run the pipeline.
          You can use the repo&apos;s bundled sample data or your own files.
        </p>
      </div>

      {submitError && (
        <div className="alert-banner alert-banner--danger" role="alert">
          {submitError}
        </div>
      )}

      <Card title="1 · Job description">
        <JdInput
          mode={jdMode}
          pastedText={jdPasted}
          sampleJobs={sampleJobs.data?.jobs ?? []}
          selectedSampleJob={selectedSampleJob}
          sampleText={sampleText}
          fileName={jdFile?.name ?? null}
          loadingSample={loadingSample || sampleJobs.isLoading}
          onModeChange={(m) => setJdMode(m)}
          onPastedChange={setJdPasted}
          onSelectSample={(id) => setSelectedSampleJob(id)}
          onFileChange={(f) => setJdFile(f)}
        />
      </Card>

      <Card title="2 · Resumes">
        {sampleResumes.isError ? (
          <ErrorState
            message={sampleResumes.error.message}
            onRetry={() => sampleResumes.refetch()}
          />
        ) : (
          <ResumeInput
            uploadedFiles={uploadedFiles}
            sampleResumes={sampleResumes.data?.resumes ?? []}
            onAddFiles={(files) =>
              setUploadedFiles((prev) => [...prev, ...files])
            }
            onRemoveFile={(i) =>
              setUploadedFiles((prev) => prev.filter((_, idx) => idx !== i))
            }
            onToggleSample={(name) =>
              setSelectedSampleResumes((prev) =>
                prev.includes(name)
                  ? prev.filter((n) => n !== name)
                  : [...prev, name],
              )
            }
          />
        )}
      </Card>

      <div className="row">
        <button className="btn btn--primary" disabled={!canSubmit} onClick={handleSubmit}>
          {submitting ? "Submitting…" : "Run screening"}
        </button>
        {!canSubmit && (
          <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>
            Add at least one resume and a job description to continue.
          </span>
        )}
      </div>
    </div>
  );
}