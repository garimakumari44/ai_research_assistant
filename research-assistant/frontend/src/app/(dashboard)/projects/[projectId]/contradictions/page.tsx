import { AppShell } from '../../../components/app-shell';
import { PaperView } from '../../../components/paper-view';
import { papers } from '../../../components/lib/mock-data';

export function generateStaticParams() {
  return papers.map((p) => ({ paperId: p.id }));
}

export default function Page({ params }: { params: { paperId: string } }) {
  return (
    <AppShell>
      <PaperView paperId={params.paperId} />
    </AppShell>
  );
}
