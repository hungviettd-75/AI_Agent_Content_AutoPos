import pandas as pd
from database.models.posts import PostModel

class PostRepository:
    @staticmethod
    def get_all_posts(workspace_id: int = None) -> pd.DataFrame:
        return PostModel.list_by_workspace(workspace_id=workspace_id, limit=100)

    @staticmethod
    def add_post(date: str, platform: str, topic: str, content: str, status: str, content_type: str, workspace_id: int = None, created_by: int = None) -> int:
        return PostModel.create(
            content=content,
            platform=platform.lower() if platform else "facebook",
            content_type=content_type,
            topic=topic,
            title=topic[:100] if topic else "Untitled Post",
            status=status.lower() if status else "draft",
            workspace_id=workspace_id,
            created_by=created_by
        )
