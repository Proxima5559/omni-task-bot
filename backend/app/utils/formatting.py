import html
from app.models.task import Task, TaskStatus

STATUS_LABEL = {
    TaskStatus.PENDING: "⏳ Pending",
    TaskStatus.IN_PROGRESS: "🚧 In progress",
    TaskStatus.COMPLETED: "✅ Completed",
}


def format_task(task: Task) -> str:
    title = html.escape(task.title)
    
    lines = [
        f"{STATUS_LABEL[task.status]}",
        f"#{task.id} <b>{title}</b>"
    ]
    
    if task.description and task.description.strip():
        description = html.escape(task.description.strip())
        lines.append(f"📝 <i>{description}</i>")
        
    return "\n".join(lines)