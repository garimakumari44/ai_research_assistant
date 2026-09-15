import { ProjectLayout } from '../../../components/project-layout';
import { ProjectMap } from '../../../components/project-views/project-map';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectMap projectId={params.projectId} />
    </ProjectLayout>
  );
}
