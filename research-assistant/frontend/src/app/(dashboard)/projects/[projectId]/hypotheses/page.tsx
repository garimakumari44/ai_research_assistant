import { ProjectLayout } from '../../../components/project-layout';
import { ProjectHypotheses } from '../../../components/project-views/project-hypotheses';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectHypotheses projectId={params.projectId} />
    </ProjectLayout>
  );
}
