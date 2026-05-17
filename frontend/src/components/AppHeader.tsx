type AppHeaderProps = {
  retentionMessage: string;
};

export function AppHeader({ retentionMessage }: AppHeaderProps) {
  return (
    <header className="flex flex-col gap-4 rounded-3xl border border-forensic-border bg-forensic-panel/70 p-5 shadow-forensic backdrop-blur md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.28em] text-forensic-blue">Deepfake Forensics</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white md:text-5xl">ML evidence review workstation</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-forensic-muted md:text-base">
          Upload media, inspect frame-level fake probabilities, identify suspicious frames, and prepare audit-ready reports.
        </p>
      </div>
      <div className="rounded-2xl border border-forensic-blue/35 bg-forensic-blue/10 p-4 text-sm text-sky-100 md:max-w-sm">{retentionMessage}</div>
    </header>
  );
}
