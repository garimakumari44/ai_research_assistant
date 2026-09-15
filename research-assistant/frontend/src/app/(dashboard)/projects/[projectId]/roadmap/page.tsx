import { ProjectLayout } from '../../../components/project-layout';
import { ProjectRoadmap } from '../../../components/project-views/project-roadmap';

export default function Page({ params }: { params: { projectId: string } }) {
  return (
    <ProjectLayout projectId={params.projectId}>
      <ProjectRoadmap projectId={params.projectId} />
    </ProjectLayout>
  );
}
