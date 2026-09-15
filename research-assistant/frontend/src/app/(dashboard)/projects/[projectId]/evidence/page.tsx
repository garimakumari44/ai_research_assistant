import { ProjectLayout } from '../../../components/project-layout';
import { ProjectEvidence } from '../../../components/project-views/project-evidence';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectEvidence projectId={params.projectId} />
    </ProjectLayout>
  );
}
