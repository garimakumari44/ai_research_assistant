import { ProjectLayout } from '../../../components/project-layout';
import { ProjectFrontier } from '../../../components/project-views/project-frontier';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectFrontier projectId={params.projectId} />
    </ProjectLayout>
  );
}
