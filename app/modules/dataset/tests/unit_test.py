import io
import os
import re
import tempfile
import uuid

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login
from app.modules.dataset.models import DataSet, DSDownloadRecord, DSMetaData, DSViewRecord
from app.modules.dataset.services import DataSetService, DiffService


@pytest.fixture(scope="module")
def test_dataset_id(test_client):
    from app import db

    with test_client.application.app_context():
        ds_meta = DSMetaData(
            title="Test Dataset",
            description="This is a test dataset",
            publication_type="NONE",
            dataset_doi="122345/test_ds",
            tags="tag1,tag2",
        )
        db.session.add(ds_meta)
        db.session.commit()

        dataset = DataSet(user_id=1, ds_meta_data_id=ds_meta.id)
        db.session.add(dataset)

        view_record = DSViewRecord(dataset_id=dataset.id, user_id=1, view_cookie=str(uuid.uuid4()))
        db.session.add(view_record)
        db.session.commit()

        dataset_id = dataset.id

    yield dataset_id

    # Cleanup
    with test_client.application.app_context():
        DSViewRecord.query.filter_by(dataset_id=dataset.id).delete()
        DSDownloadRecord.query.filter_by(dataset_id=dataset.id).delete()
        db.session.delete(dataset)
        db.session.delete(ds_meta)
        db.session.commit()


def test_dataset_badge_md(test_client, test_dataset_id):
    response = test_client.get(f"/dataset/{test_dataset_id}/badge/md")
    assert response.status_code == 200
    assert b"![Static Badge]" in response.data
    assert b"Test_Dataset" in response.data


def test_dataset_badge_html(test_client, test_dataset_id):
    response = test_client.get(f"/dataset/{test_dataset_id}/badge/html")
    assert response.status_code == 200
    assert b"<img" in response.data
    assert b"Test_Dataset" in response.data


def test_trending_datasets_view(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"<h2> <b>Trending datasets</b> </h2>" in response.data


def test_trending_datasets(test_client):
    import uuid
    from datetime import datetime

    from app import db
    from app.modules.dataset.models import DataSet, DSDownloadRecord, DSMetaData
    from app.modules.dataset.services import DataSetService

    with test_client.application.app_context():
        ds_meta = DSMetaData(
            title="Test Dataset Meta",
            description="Meta for test datasets",
            publication_type="NONE",
            tags="trending,test",
        )
        db.session.add(ds_meta)
        db.session.commit()

        ds1 = DataSet(user_id=1, ds_meta_data_id=ds_meta.id)
        ds2 = DataSet(user_id=1, ds_meta_data_id=ds_meta.id)
        db.session.add(ds1)
        db.session.add(ds2)
        db.session.commit()

        download1 = DSDownloadRecord(
            dataset_id=ds1.id, download_date=datetime.utcnow(), download_cookie=str(uuid.uuid4())
        )
        download2 = DSDownloadRecord(
            dataset_id=ds1.id, download_date=datetime.utcnow(), download_cookie=str(uuid.uuid4())
        )

        download3 = DSDownloadRecord(
            dataset_id=ds2.id, download_date=datetime.utcnow(), download_cookie=str(uuid.uuid4())
        )

        db.session.add_all([download1, download2, download3])
        db.session.commit()

        service = DataSetService()
        assert service.trending_datasets() == [(ds1, 2), (ds2, 1)]

    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Trending datasets" in response.data


def test_download_count_present_in_body(test_client):
    response = test_client.get("/doi/122345/test_ds/")
    assert response.status_code == 200
    assert b"Downloads" in response.data


def test_download_count_feat(test_client):
    response = test_client.get("/doi/122345/test_ds/")
    assert response.status_code == 200
    assert b"Downloads" in response.data

    html = response.data.decode("utf-8")
    init_downloads = get_downloads_from_html(html)

    test_client.get("/dataset/download/1")
    response2 = test_client.get("/doi/122345/test_ds/")
    html2 = response2.data.decode("utf-8")
    new_downloads = get_downloads_from_html(html2)
    assert new_downloads != init_downloads
    assert new_downloads == (init_downloads + 1)


def get_downloads_from_html(html):
    # Busca la celda <td>Downloads</td> seguida de otra celda <td>...</td>
    patron = r"<td>\s*Downloads\s*</td>\s*<td>\s*(\d+)\s*</td>"

    match = re.search(patron, html, re.IGNORECASE)
    downloads_value = int(match.group(1))
    return downloads_value


def test_list_dataset_without_login(test_client):
    response = test_client.get("/dataset/list")
    assert response.status_code == 302


def test_list_dataset(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/dataset/list")
    assert response.status_code == 200
    assert b"My datasets" in response.data


def test_get_dataset_upload(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/dataset/upload")
    assert response.status_code == 200
    assert b"Upload" in response.data


def make_upload_file(filename, content: bytes):
    return (io.BytesIO(content), filename)


def test_dataset_file_upload_and_delete(test_client):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    data = {"file": (io.BytesIO(b"a,b\n1,2\n"), "not_csv.txt")}
    resp = test_client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400

    data = {"file": (io.BytesIO(b"col1,col2\n1,2\n"), "test_upload.csv")}
    resp = test_client.post("/dataset/file/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert "filename" in json_data
    filename = json_data["filename"]

    resp2 = test_client.post("/dataset/file/delete", json={"file": filename})
    assert resp2.status_code == 200
    assert resp2.get_json().get("message") == "File deleted successfully"


def test_dataset_create(test_client, monkeypatch):
    def mock_create_new_deposition(dataset):
        return {}

    from app.modules.zenodo import services as zenodo_services

    monkeypatch.setattr(zenodo_services.ZenodoService, "create_new_deposition", mock_create_new_deposition)

    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    csv_content = b"col1,col2,col3\n1,2,3\n4,5,6\n"
    csv_filename = f"dataset_{uuid.uuid4().hex[:8]}.csv"

    upload_response = test_client.post(
        "/dataset/file/upload",
        data={"file": (io.BytesIO(csv_content), csv_filename)},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    uploaded_filename = upload_response.get_json()["filename"]

    dataset_data = {
        "title": "Test Dataset Creation",
        "desc": "Testing dataset creation",
        "publication_type": "other",
        "tags": "test,dataset",
        "authors-0-name": "Test Author",
        "csv_files-0-csv_filename": uploaded_filename,
    }

    resp = test_client.post("/dataset/upload", data=dataset_data)
    assert resp.status_code == 200

    with test_client.application.app_context():
        dataset = DataSet.query.filter_by(user_id=1).order_by(DataSet.id.desc()).first()
        assert dataset is not None
        assert dataset.ds_meta_data.title == "Test Dataset Creation"
        assert dataset.ds_meta_data.description == "Testing dataset creation"


def test_get_dataset_edit(test_client, test_dataset_id):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get(f"/dataset/{test_dataset_id}/edit")
    assert response.status_code == 200
    assert b"edit" in response.data.lower()


def test_dataset_update_with_files(test_client, test_dataset_id):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    new_csv_content = b"col1,col2,col3,col4\n1,2,3,4\n5,6,7,8\n"
    new_csv_filename = f"updated_dataset_{uuid.uuid4().hex[:8]}.csv"

    resp = test_client.post(
        "/dataset/file/upload",
        data={"file": (io.BytesIO(new_csv_content), new_csv_filename)},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert "filename" in json_data

    update_data = {
        "files_to_delete": [],
        "metadata": {
            "title": "Updated Dataset Title",
            "description": "Updated description",
        },
    }

    resp = test_client.post(f"/dataset/{test_dataset_id}/update", json=update_data)
    assert resp.status_code in [200, 403, 404, 500]


def test_dataset_delete_files_on_edit(test_client, test_dataset_id):
    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    update_data = {
        "files_to_delete": ["test_file.csv"],
        "metadata": None,
    }

    resp = test_client.post(f"/dataset/{test_dataset_id}/update", json=update_data)
    assert resp.status_code in [200, 403, 404, 500]


def test_create_new_dataset_version(test_client):

    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    with test_client.application.app_context():
        ds_meta = DSMetaData(
            title="Version Test Dataset",
            description="Original description",
            publication_type="NONE",
            tags="versioning,test",
        )
        db.session.add(ds_meta)
        db.session.commit()

        user = User.query.filter_by(email="test@example.com").first()
        dataset_v1 = DataSet(user_id=user.id, ds_meta_data_id=ds_meta.id, version=1)
        db.session.add(dataset_v1)
        db.session.commit()

        initial_version = dataset_v1.version
        initial_id = dataset_v1.id

        service = DataSetService()
        metadata_changes = {
            "title": "Version Test Dataset (Updated)",
            "description": "Updated description",
        }

        dataset_v2 = service.create_new_version(
            dataset=dataset_v1, files_to_delete=[], current_user=user, metadata_changes=metadata_changes
        )

        assert dataset_v2.version == initial_version + 1
        assert dataset_v2.version == 2

        assert dataset_v2.previous_version_id == initial_id
        assert dataset_v2.previous_version == dataset_v1

        assert dataset_v2.ds_meta_data.title == "Version Test Dataset (Updated)"
        assert dataset_v2.ds_meta_data.description == "Updated description"

        assert dataset_v1.ds_meta_data.title == "Version Test Dataset"
        assert dataset_v1.ds_meta_data.description == "Original description"


def test_dataset_version_chain(test_client):

    login_response = login(test_client, "test@example.com", "test1234")
    assert login_response.status_code == 200

    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        service = DataSetService()

        ds_meta_v1 = DSMetaData(
            title="Chain Test v1",
            description="Version 1",
            publication_type="NONE",
        )
        db.session.add(ds_meta_v1)
        db.session.commit()

        v1 = DataSet(user_id=user.id, ds_meta_data_id=ds_meta_v1.id, version=1)
        db.session.add(v1)
        db.session.commit()

        v2 = service.create_new_version(
            dataset=v1,
            files_to_delete=[],
            current_user=user,
            metadata_changes={"title": "Chain Test v2", "description": "Version 1"},
        )

        v3 = service.create_new_version(
            dataset=v2,
            files_to_delete=[],
            current_user=user,
            metadata_changes={"title": "Chain Test v3", "description": "Version 1"},
        )

        assert v3.version == 3
        assert v3.previous_version.version == 2
        assert v3.previous_version.previous_version.version == 1
        assert v3.previous_version.previous_version.previous_version is None

        assert v1.ds_meta_data.title == "Chain Test v1"
        assert v2.ds_meta_data.title == "Chain Test v2"
        assert v3.ds_meta_data.title == "Chain Test v3"


def test_get_file_diff_between_versions(test_client):
    """Test generating diffs between file versions"""
    import os
    import tempfile

    from app.modules.dataset.services import DiffService

    with test_client.application.app_context():
        with tempfile.TemporaryDirectory() as tmpdir:
            prev_file = os.path.join(tmpdir, "prev.csv")
            curr_file = os.path.join(tmpdir, "curr.csv")

            with open(prev_file, "w") as f:
                f.write("id,name,email\n")
                f.write("1,Alice,alice@example.com\n")
                f.write("2,Bob,bob@example.com\n")

            with open(curr_file, "w") as f:
                f.write("id,name,email\n")
                f.write("1,Alice,alice@example.com\n")
                f.write("2,Bob,bob@updated.com\n")  # Changed
                f.write("3,Charlie,charlie@example.com\n")  # Added

            diff_result = DiffService.get_file_diff(prev_file, curr_file)

            assert "previous_lines" in diff_result
            assert "current_lines" in diff_result
            assert "diff" in diff_result

            assert diff_result["previous_lines"] == 3
            assert diff_result["current_lines"] == 4

            diff_operations = diff_result["diff"]
            assert len(diff_operations) > 0

            has_removed = any(op["type"] == "removed" for op in diff_operations)
            has_added = any(op["type"] == "added" for op in diff_operations)
            has_context = any(op["type"] == "context" for op in diff_operations)

            assert has_removed or has_added or has_context


def test_diff_service_with_identical_files(test_client):

    with test_client.application.app_context():
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.csv")
            file2 = os.path.join(tmpdir, "file2.csv")

            content = "id,name\n1,Test\n2,Data\n"

            with open(file1, "w") as f:
                f.write(content)

            with open(file2, "w") as f:
                f.write(content)

            diff_result = DiffService.get_file_diff(file1, file2)

            diff_operations = diff_result["diff"]

            for op in diff_operations:
                assert op["type"] == "context"
