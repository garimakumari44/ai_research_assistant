import { ProjectLayout } from '../components/project-layout';
import { ProjectOverview } from '../components/project-views/project-overview';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectOverview projectId={params.projectId} />
    </ProjectLayout>
  );
}
