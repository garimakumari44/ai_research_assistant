import { ProjectLayout } from '../../../components/project-layout';
import { ProjectTrends } from '../../../components/project-views/project-trends';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectTrends projectId={params.projectId} />
    </ProjectLayout>
  );
}
