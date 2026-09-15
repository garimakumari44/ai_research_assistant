import { ProjectLayout } from '../../../components/project-layout';
import { ProjectGaps } from '../../../components/project-views/project-gaps';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectGaps projectId={params.projectId} />
    </ProjectLayout>
  );
}
