export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to BrandOS. Your AI content engine is ready.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border p-4">
          <h3 className="font-semibold">Quick Brief</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Generate a daily content brief with one click.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <h3 className="font-semibold">Recent Content</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Your recently published and drafted pieces.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <h3 className="font-semibold">Analytics Snapshot</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Content performance at a glance.
          </p>
        </div>
      </div>
    </div>
  );
}
