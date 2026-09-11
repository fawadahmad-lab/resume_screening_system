export type JdMode = "paste" | "sample" | "upload";

interface JdInputProps {
  mode: JdMode;
  pastedText: string;
  sampleJobs: { id: string; name: string }[];
  selectedSampleJob: string | null;
  sampleText: string;
  fileName: string | null;
  loadingSample: boolean;
  onModeChange: (mode: JdMode) => void;
  onPastedChange: (text: string) => void;
  onSelectSample: (id: string) => void;
  onFileChange: (file: File | null) => void;
}

const TABS: { key: JdMode; label: string }[] = [
  { key: "paste", label: "Paste" },
  { key: "sample", label: "Sample JD" },
  { key: "upload", label: "Upload" },
];

export function JdInput({
  mode,
  pastedText,
  sampleJobs,
  selectedSampleJob,
  sampleText,
  fileName,
  loadingSample,
  onModeChange,
  onPastedChange,
  onSelectSample,
  onFileChange,
}: JdInputProps) {
  return (
    <div className="stack stack--sm" role="group" aria-label="Job description input">
      <div className="row" role="tablist" aria-label="Job description source">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={mode === t.key}
            className={`btn ${mode === t.key ? "btn--primary" : "btn--secondary"}`}
            onClick={() => onModeChange(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {mode === "paste" && (
        <div className="field">
          <label className="field__label" htmlFor="jd-paste">
            Job description
          </label>
          <textarea
            id="jd-paste"
            className="textarea"
            placeholder="Paste the job description…"
            value={pastedText}
            onChange={(e) => onPastedChange(e.target.value)}
          />
        </div>
      )}

      {mode === "sample" && (
        <div className="field">
          <span className="badge badge--sample" style={{ alignSelf: "flex-start" }}>
            Sample data
          </span>
          <div className="stack stack--sm">
            {sampleJobs.map((job) => (
              <label
                key={job.id}
                className="row"
                style={{ cursor: "pointer" }}
              >
                <input
                  type="radio"
                  name="sample-job"
                  checked={selectedSampleJob === job.id}
                  onChange={() => onSelectSample(job.id)}
                />
                <span className="mono">{job.name}</span>
              </label>
            ))}
          </div>
          {selectedSampleJob && (
            <div style={{ marginTop: "var(--sp-2)" }}>
              <p className="muted" style={{ fontSize: "var(--fs-xs)", marginBottom: "var(--sp-1)" }}>
                Preview of {selectedSampleJob}:
              </p>
              {loadingSample ? (
                <p className="muted">Loading…</p>
              ) : (
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    fontFamily: "var(--font-mono)",
                    fontSize: "var(--fs-xs)",
                    padding: "var(--sp-3)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                    background: "var(--color-surface-muted)",
                    maxHeight: "160px",
                    overflowY: "auto",
                  }}
                >
                  {sampleText}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {mode === "upload" && (
        <div className="field">
          <label className="field__label" htmlFor="jd-file">
            Job description file (txt, pdf, docx)
          </label>
          <input
            id="jd-file"
            type="file"
            accept=".txt,.pdf,.docx,.md"
            onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
          />
          {fileName && <p className="mono faint">{fileName}</p>}
        </div>
      )}
    </div>
  );
}