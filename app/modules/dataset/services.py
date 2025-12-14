import csv
import hashlib
import logging
import os
import shutil
import uuid
from typing import Optional

from flask import request

from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import CSVFile, DataSet, DSMetaData, DSViewRecord
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()

    def move_csv_files(self, dataset: DataSet):
        """
        Move CSV files from temp folder to the dataset directory.
        Also creates CSVFile database entries for any new files found in temp folder.
        """
        current_user = AuthenticationService().get_authenticated_user()
        source_dir = current_user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

        os.makedirs(dest_dir, exist_ok=True)

        # Move existing dataset files
        for csv_file in dataset.csv_files:
            src_path = os.path.join(source_dir, csv_file.name)
            dst_path = os.path.join(dest_dir, csv_file.name)
            if os.path.exists(src_path):
                shutil.move(src_path, dst_path)

        # Add any remaining files in source_dir to the dataset
        if os.path.exists(source_dir):
            for filename in os.listdir(source_dir):
                if filename.endswith(".csv"):
                    src_path = os.path.join(source_dir, filename)
                    dst_path = os.path.join(dest_dir, filename)

                    # Move file to destination
                    shutil.move(src_path, dst_path)

                    # Create CSVFile entry if it doesn't exist
                    existing = CSVFile.query.filter_by(name=filename, dataset_id=dataset.id).first()

                    if not existing:
                        checksum, size = calculate_checksum_and_size(dst_path)
                        csv_file = CSVFile(name=filename, checksum=checksum, size=size, dataset_id=dataset.id)
                        self.repository.session.add(csv_file)
                        dataset.csv_files.append(csv_file)

            self.repository.session.commit()

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_synchronized(current_user_id)

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repostory.total_dataset_views()

    def trending_datasets(self) -> list[tuple[DataSet, int]]:
        return self.dsdownloadrecord_repository.get_trending_datasets()

    def create_from_form(self, form, current_user) -> DataSet:
        main_author = {
            "name": f"{current_user.
                       profile.surname},{current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }
        try:
            logger.info(f"Creating dsmetadata...: {form.get_dsmetadata()}")
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())
            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            dataset = self.create(commit=False, user_id=current_user.id, ds_meta_data_id=dsmetadata.id)

            # Add CSV files to the dataset
            for csv_file_field in form.csv_files:
                csv_filename = csv_file_field.csv_filename.data
                file_path = os.path.join(current_user.temp_folder(), csv_filename)
                checksum, size = calculate_checksum_and_size(file_path)

                csv_file = CSVFile(name=csv_filename, checksum=checksum, size=size, dataset_id=dataset.id)
                dataset.csv_files.append(csv_file)

            self.repository.session.commit()
        except Exception as exc:
            logger.info(f"Exception creating dataset from form...: {exc}")
            self.repository.session.rollback()
            raise exc
        return dataset

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

    def get_dataset_doi_url(self, dataset: DataSet) -> str:
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"

    def validate_csv_content(file):

        try:
            file_contents = file.read().decode("utf-8").splitlines()

            if not file_contents:
                return False, "CSV file is empty or not in UTF-8 format."

            # Use the csv module to check structure
            reader = csv.reader(file_contents)
            header = next(reader)

            if not header or not any(header):
                return False, "CSV header row cannot be empty."

            # Check for at least one data row
            try:
                next(reader)
            except StopIteration:
                return (False,)
                "CSV must contain a header and at least one data row."

            file.seek(0)

            return True, None

        except UnicodeDecodeError:
            file.seek(0)
            return False, "Error: CSV file must be UTF-8 encoded."
        except Exception as e:
            file.seek(0)
            return False, f"Error validating CSV content: {type(e).__name__}."

    def get_related_datasets(self, dataset_id: int) -> list:
        target_dataset = self.repository.get_by_id(dataset_id)
        if not target_dataset or not target_dataset.ds_meta_data:
            return []

        target_tags = set()
        if target_dataset.ds_meta_data.tags:
            target_tags = {t.strip().lower() for t in target_dataset.ds_meta_data.tags.split(",")}

        target_authors = {a.name.strip().lower() for a in target_dataset.ds_meta_data.authors}

        all_datasets = self.repository.get_all()

        candidates = []

        for ds in all_datasets:
            if ds.id == target_dataset.id:
                continue

            if not ds.ds_meta_data:
                continue

            score = 0

            if ds.ds_meta_data.tags:
                ds_tags = {t.strip().lower() for t in ds.ds_meta_data.tags.split(",")}
                common_tags = target_tags.intersection(ds_tags)
                score += len(common_tags)

            ds_authors = {a.name.strip().lower() for a in ds.ds_meta_data.authors}
            common_authors = target_authors.intersection(ds_authors)
            score += len(common_authors)

            if score > 0:
                candidates.append({"dataset": ds, "score": score})

        candidates.sort(
            key=lambda x: (x["score"], x["dataset"].ds_meta_data.downloads, x["dataset"].created_at), reverse=True
        )

        return [item["dataset"] for item in candidates[:4]]

    def create_new_version(
        self, dataset: DataSet, files_to_delete: list, current_user, metadata_changes: dict = None
    ) -> DataSet:
        try:
            # Prepare metadata values - use updated values if provided, otherwise keep original
            metadata_values = {
                "title": metadata_changes.get("title") if metadata_changes else dataset.ds_meta_data.title,
                "description": (
                    metadata_changes.get("description") if metadata_changes else dataset.ds_meta_data.description
                ),
                "publication_type": (
                    self._convert_publication_type(metadata_changes.get("publication_type"))
                    if metadata_changes and metadata_changes.get("publication_type")
                    else dataset.ds_meta_data.publication_type
                ),
                "publication_doi": (
                    metadata_changes.get("publication_doi")
                    if metadata_changes
                    else dataset.ds_meta_data.publication_doi
                ),
                "dataset_doi": dataset.ds_meta_data.dataset_doi,
                "tags": (metadata_changes.get("tags") if metadata_changes else dataset.ds_meta_data.tags),
                "ds_metrics_id": dataset.ds_meta_data.ds_metrics_id,
                "deposition_id": dataset.ds_meta_data.deposition_id,
                "downloads": dataset.ds_meta_data.downloads,
                "commit": False,
            }

            new_metadata = self.dsmetadata_repository.create(**metadata_values)

            for author in dataset.ds_meta_data.authors:
                new_author = self.author_repository.create(
                    commit=False,
                    ds_meta_data_id=new_metadata.id,
                    name=author.name,
                    affiliation=author.affiliation,
                    orcid=author.orcid,
                )
                new_metadata.authors.append(new_author)

            new_dataset = self.create(
                commit=False,
                user_id=current_user.id,
                ds_meta_data_id=new_metadata.id,
                version=dataset.version + 1,
                previous_version_id=dataset.id,
            )

            self.repository.session.commit()

            working_dir = os.getenv("WORKING_DIR", "")
            old_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")
            new_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{new_dataset.id}")

            os.makedirs(new_dir, exist_ok=True)

            for csv_file in dataset.csv_files:
                if csv_file.id not in files_to_delete:
                    old_file_path = os.path.join(old_dir, csv_file.name)
                    new_file_path = os.path.join(new_dir, csv_file.name)

                    if os.path.exists(old_file_path):
                        shutil.copy2(old_file_path, new_file_path)

                        # Create new CSVFile entry
                        checksum, size = calculate_checksum_and_size(new_file_path)
                        new_csv_file = CSVFile(
                            name=csv_file.name, checksum=checksum, size=size, dataset_id=new_dataset.id
                        )
                        new_dataset.csv_files.append(new_csv_file)

            self.repository.session.commit()

            return new_dataset

        except Exception as exc:
            logger.exception(f"Exception creating new dataset version: {exc}")
            self.repository.session.rollback()
            raise exc

    def _convert_publication_type(self, value: str):
        """Convert publication type string to enum"""
        from app.modules.dataset.models import PublicationType

        for pt in PublicationType:
            if pt.value == value:
                return pt
        return PublicationType.NONE


class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new
        else:
            return None


class SizeService:

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        else:
            return f"{round(size / (1024 ** 3), 2)} GB"


class DiffService:
    """Service for generating diffs between file versions"""

    @staticmethod
    def get_file_diff(previous_file_path: str, current_file_path: str):
        """
        Generate a detailed diff between two CSV files.
        Returns structured diff data with operation types: added, removed, context.
        """
        import difflib

        try:
            with open(previous_file_path, "r", encoding="utf-8") as f:
                previous_lines = f.readlines()
        except Exception as e:
            logger.error(f"Error reading previous file: {e}")
            previous_lines = []

        try:
            with open(current_file_path, "r", encoding="utf-8") as f:
                current_lines = f.readlines()
        except Exception as e:
            logger.error(f"Error reading current file: {e}")
            current_lines = []

        # Use difflib to generate a unified diff
        differ = difflib.unified_diff(previous_lines, current_lines, lineterm="")
        diff_lines = list(differ)

        # Parse the diff output into structured format
        diff_data = DiffService._parse_unified_diff(diff_lines, previous_lines, current_lines)

        return {
            "previous_lines": len(previous_lines),
            "current_lines": len(current_lines),
            "diff": diff_data,
        }

    @staticmethod
    def _parse_unified_diff(diff_lines, previous_lines, current_lines):
        """
        Parse unified diff format into a more usable structure.
        Returns a list with structured diff information.
        """
        result = []
        prev_idx = 0
        curr_idx = 0

        # Skip the header lines
        for line in diff_lines[2:]:
            if line.startswith("@@"):
                continue

            if line.startswith("-"):
                # Removed line
                line_content = line[1:]
                result.append(
                    {
                        "type": "removed",
                        "line_number": prev_idx + 1,
                        "content": line_content,
                    }
                )
                prev_idx += 1
            elif line.startswith("+"):
                # Added line
                line_content = line[1:]
                result.append(
                    {
                        "type": "added",
                        "line_number": curr_idx + 1,
                        "content": line_content,
                    }
                )
                curr_idx += 1
            else:
                # Context line (unchanged)
                result.append(
                    {
                        "type": "context",
                        "previous_line_number": prev_idx + 1,
                        "current_line_number": curr_idx + 1,
                        "content": line[1:] if line.startswith(" ") else line,
                    }
                )
                prev_idx += 1
                curr_idx += 1

        return result
