type AppHeaderProps = {
  retentionMessage: string;
};

export function AppHeader({ retentionMessage }: AppHeaderProps) {
  return (
    <header className="flex flex-col gap-3 rounded-2xl border border-forensic-border bg-forensic-panel/70 p-4 shadow-forensic backdrop-blur md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-forensic-blue">Deepfake Forensics</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white md:text-4xl">ML evidence review workstation</h1>
        <p className="mt-2 max-w-3xl text-sm leading-5 text-forensic-muted">
          Upload media, inspect frame-level fake probabilities, identify suspicious frames, and prepare audit-ready reports.
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium text-sky-100">
          <span className="rounded-full border border-forensic-blue/40 bg-forensic-blue/10 px-3 py-1">Upload complete</span>
          <span className="rounded-full border border-forensic-blue/40 bg-forensic-blue/10 px-3 py-1">Model inference complete</span>
          <span className="rounded-full border border-forensic-blue/40 bg-forensic-blue/10 px-3 py-1">Report ready</span>
        </div>
      </div>
      <div className="rounded-2xl border border-forensic-blue/35 bg-forensic-blue/10 p-3 text-xs leading-5 text-sky-100 md:max-w-xs">{retentionMessage}</div>
    </header>
  );
}
