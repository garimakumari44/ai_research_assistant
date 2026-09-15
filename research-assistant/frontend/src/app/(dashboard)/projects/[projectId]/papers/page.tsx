import { ProjectLayout } from '../../../components/project-layout';
import { ProjectPapers } from '../../../components/project-views/project-papers';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectPapers projectId={params.projectId} />
    </ProjectLayout>
  );
}
