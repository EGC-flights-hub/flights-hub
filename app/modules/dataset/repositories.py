import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from flask_login import current_user
from sqlalchemy import desc, func

from app.modules.dataset.models import Author, DataSet, DOIMapping, DSDownloadRecord, DSMetaData, DSViewRecord
from core.repositories.BaseRepository import BaseRepository

logger = logging.getLogger(__name__)


class AuthorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Author)


class DSDownloadRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSDownloadRecord)

    def total_dataset_downloads(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0

    def get_trending_datasets(self):
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        NUMBER_OF_TRENDING_DATASETS = 3
        return (
            self.model.query.join(DataSet, self.model.dataset_id == DataSet.id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(self.model.download_date >= one_week_ago)
            .with_entities(DataSet, func.count().label("download_count"))
            .group_by(DataSet)
            .order_by(desc("download_count"))
            .limit(NUMBER_OF_TRENDING_DATASETS)
            .all()
        )


class DSMetaDataRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSMetaData)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        # Get the most recent version by joining with DataSet and filtering by latest version
        return (
            self.model.query.join(DataSet, self.model.id == DataSet.ds_meta_data_id)
            .filter(self.model.dataset_doi == doi)
            .filter(~DataSet.next_version.any())  # Only get the latest version
            .first()
        )


class DSViewRecordRepository(BaseRepository):
    def __init__(self):
        super().__init__(DSViewRecord)

    def total_dataset_views(self) -> int:
        max_id = self.model.query.with_entities(func.max(self.model.id)).scalar()
        return max_id if max_id is not None else 0

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.model.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            view_cookie=user_cookie,
        ).first()

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset.id,
            view_date=datetime.now(timezone.utc),
            view_cookie=user_cookie,
        )


class DataSetRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def get_all(self):
        return self.model.query.all()

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(DataSet.user_id == current_user_id, DSMetaData.dataset_doi.isnot(None))
            .filter(~self.model.next_version.any())  # Only get latest versions
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData)
            .filter(DataSet.user_id == current_user_id, DSMetaData.dataset_doi.is_(None))
            .filter(~self.model.next_version.any())  # Only get latest versions
            .order_by(self.model.created_at.desc())
            .all()
        )

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return (
            self.model.query.join(DSMetaData).filter(DataSet.id == dataset_id, DSMetaData.dataset_doi.is_(None)).first()
        )

    def count_synchronized_datasets(self):
        return self.model.query.join(DSMetaData).filter(DSMetaData.dataset_doi.isnot(None)).count()

    def count_unsynchronized_datasets(self):
        return self.model.query.join(DSMetaData).filter(DSMetaData.dataset_doi.is_(None)).count()

    def latest_synchronized(self):
        return (
            self.model.query.join(DSMetaData)
            .filter(~self.model.next_version.any())  # Only get latest versions
            .order_by(desc(self.model.id))
            .limit(5)
            .all()
        )

    def get_trending_datasets(self):
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        NUMBER_OF_TRENDING_DATASETS = 3
        return (
            DSDownloadRecord.query.join(DataSet, DSDownloadRecord.dataset_id == DataSet.id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSDownloadRecord.download_date >= one_week_ago)
            .with_entities(DSMetaData.title, func.count().label("download_count"))
            .group_by(DSMetaData.title)
            .order_by(desc("download_count"))
            .limit(NUMBER_OF_TRENDING_DATASETS)
            .all()
        )


class DOIMappingRepository(BaseRepository):
    def __init__(self):
        super().__init__(DOIMapping)

    def get_new_doi(self, old_doi: str) -> str:
        return self.model.query.filter_by(dataset_doi_old=old_doi).first()
