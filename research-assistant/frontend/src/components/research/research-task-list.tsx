import type {
  ResearchTask,
} from "@/research/types";

import { ResearchTask as ResearchTaskView } from "./research-task";

export function ResearchTaskList({
  tasks,
}: {
  tasks: ResearchTask[];
}) {
  if (!tasks.length) {
    return null;
  }

  return (
    <section>
      <div className="mb-3">
        <h2 className="text-sm font-semibold">
          Research Tasks
        </h2>

        <p className="mt-1 text-xs text-muted-foreground">
          Multi-step execution across the research knowledge base.
        </p>
      </div>

      <div className="space-y-2">
        {tasks.map((task) => (
          <ResearchTaskView
            key={task.id}
            task={task}
          />
        ))}
      </div>
    </section>
  );
}