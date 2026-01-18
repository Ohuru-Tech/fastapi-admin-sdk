from typing import Any, Optional


class Resource:
    def __init__(self, name: str, verbose_name_plural: str):
        self.name = name
        self.verbose_name_plural = verbose_name_plural

    async def create(self, data: dict):
        pass

    async def update(self, lookup: Any, data: dict):
        pass

    async def delete(self, lookup: Any):
        pass

    async def list(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[dict] = None,
        ordering: Optional[list] = None,
    ):
        pass

    async def retrieve(self, lookup: Any):
        pass
