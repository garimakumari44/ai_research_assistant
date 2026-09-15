import { AppShell } from '../../components/app-shell';
import { PaperView } from '../../components/paper-view';

export default async function Page({
  params,
}: {
  params: Promise<{ paperId: string }>;
}) {
  const { paperId } = await params;

  return (
    <AppShell>
      <PaperView paperId={paperId} />
    </AppShell>
  );
}