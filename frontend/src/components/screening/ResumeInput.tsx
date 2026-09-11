import { useRef, type DragEvent } from "react";
import { UploadCloud, X } from "lucide-react";

interface ResumeInputProps {
  uploadedFiles: File[];
  sampleResumes: string[];
  onAddFiles: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onToggleSample: (name: string) => void;
}

export function ResumeInput({
  uploadedFiles,
  sampleResumes,
  onAddFiles,
  onRemoveFile,
  onToggleSample,
}: ResumeInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length) onAddFiles(files);
  };

  return (
    <div className="stack stack--sm">
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onClick={() => inputRef.current?.click()}
        aria-label="Upload resume files. Drag and drop or press Enter to browse."
        style={{
          border: "2px dashed var(--color-border-strong)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--sp-6)",
          textAlign: "center",
          cursor: "pointer",
          background: "var(--color-surface-muted)",
        }}
      >
        <UploadCloud
          size={28}
          aria-hidden="true"
          style={{ color: "var(--color-text-faint)", marginBottom: "var(--sp-2)" }}
        />
        <p>
          <strong>Drop resumes here</strong> or click to browse
        </p>
        <p className="faint" style={{ fontSize: "var(--fs-sm)" }}>
          txt, pdf, docx — multiple files supported
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".txt,.pdf,.docx"
          style={{ display: "none" }}
          aria-hidden="true"
          onChange={(e) => onAddFiles(Array.from(e.target.files ?? []))}
        />
      </div>

      {uploadedFiles.length > 0 && (
        <ul
          className="stack stack--sm"
          style={{ listStyle: "none", margin: 0, padding: 0 }}
        >
          {uploadedFiles.map((f, i) => (
            <li key={`${f.name}-${i}`} className="row">
              <span className="mono" style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {f.name}
              </span>
              <button
                type="button"
                className="btn btn--ghost"
                aria-label={`Remove ${f.name}`}
                onClick={() => onRemoveFile(i)}
              >
                <X size={16} aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="field">
        <span className="badge badge--sample" style={{ alignSelf: "flex-start" }}>
          Sample / demo data
        </span>
        <p className="field__hint">
          Or pick from the repo&apos;s bundled synthetic resumes.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "var(--sp-2)" }}>
          {sampleResumes.map((name) => (
            <label key={name} className="row" style={{ cursor: "pointer", fontSize: "var(--fs-sm)" }}>
              <input
                type="checkbox"
                checked={sampleResumes.includes(name)}
                onChange={() => onToggleSample(name)}
              />
              <span className="mono">{name}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}