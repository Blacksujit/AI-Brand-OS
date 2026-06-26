from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.core.config import Settings


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self._endpoint = settings.storage_endpoint
        self._access_key = settings.storage_access_key
        self._secret_key = settings.storage_secret_key
        self._bucket = settings.storage_bucket
        self._region = settings.storage_region
        self._client: Any = None
        self._local_path = settings.data_dir / "storage"

    async def initialize(self) -> None:
        self._local_path.mkdir(parents=True, exist_ok=True)
        if self._is_s3_endpoint():
            import aioboto3
            session = aioboto3.Session()
            self._client = session.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region,
            )
            await self._ensure_bucket()
        else:
            self._local_path.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def upload(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        if self._client:
            await self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        else:
            file_path = self._local_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(data)
        return key

    async def download(self, key: str) -> bytes | None:
        if self._client:
            response = await self._client.get_object(
                Bucket=self._bucket, Key=key
            )
            return await response["Body"].read()
        file_path = self._local_path / key
        if not file_path.exists():
            return None
        return file_path.read_bytes()

    async def delete(self, key: str) -> bool:
        if self._client:
            await self._client.delete_object(Bucket=self._bucket, Key=key)
            return True
        file_path = self._local_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def list_keys(self, prefix: str = "") -> list[str]:
        if self._client:
            response = await self._client.list_objects_v2(
                Bucket=self._bucket, Prefix=prefix
            )
            return [obj["Key"] for obj in response.get("Contents", [])]
        base = self._local_path / prefix
        if not base.exists():
            return []
        return [
            str(p.relative_to(self._local_path))
            for p in base.rglob("*")
            if p.is_file()
        ]

    async def exists(self, key: str) -> bool:
        if self._client:
            try:
                await self._client.head_object(Bucket=self._bucket, Key=key)
                return True
            except Exception:
                return False
        return (self._local_path / key).exists()

    def _is_s3_endpoint(self) -> bool:
        return "amazonaws.com" in self._endpoint or "minio" not in self._endpoint.lower()

    async def _ensure_bucket(self) -> None:
        if not self._client:
            return
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            await self._client.create_bucket(
                Bucket=self._bucket,
                CreateBucketConfiguration={"LocationConstraint": self._region},
            )
