import pandas as pd
from database.models.knowledge import KnowledgeModel

class KnowledgeRepository:
    @staticmethod
    def _require_workspace(workspace_id: int) -> None:
        if workspace_id is None:
            raise ValueError("workspace_id is required")

    @staticmethod
    def save_knowledge_post(
        date=None, platform="", topic="", audience="",
        tool_name="", knowledge_type="", difficulty="",
        content="", summary="", status="Draft",
        workspace_id: int = 1,
        created_by: int = 1,
        folder: str = "Chung",
        collection: str = "Mặc định",
        version: str = "1.0",
        tags: list = None
    ) -> int:
        KnowledgeRepository._require_workspace(workspace_id)
        return KnowledgeModel.create(
            content=content,
            topic=topic,
            title=topic,
            summary=summary,
            knowledge_type=knowledge_type,
            ai_tool=tool_name,
            audience=audience,
            difficulty=difficulty,
            platform=platform,
            status=status,
            workspace_id=workspace_id,
            created_by=created_by,
            folder=folder,
            collection=collection,
            version=version,
            tags=tags
        )

    @staticmethod
    def get_knowledge_posts(status=None, platform=None, limit=None, workspace_id: int = None) -> pd.DataFrame:
        KnowledgeRepository._require_workspace(workspace_id)
        return KnowledgeModel.list_all(
            status=status,
            platform=platform,
            limit=limit or 50,
            workspace_id=workspace_id
        )

    @staticmethod
    def delete_knowledge_post(post_id, workspace_id: int = None) -> bool:
        KnowledgeRepository._require_workspace(workspace_id)
        return KnowledgeModel.delete(post_id, workspace_id=workspace_id)
