import re
import uuid

import pytest

from app.modules.conftest import login
from app.modules.dataset.models import DataSet, DSDownloadRecord, DSMetaData, DSViewRecord


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
        ds_meta = DSMetaData(title="Test Dataset Meta", description="Meta for test datasets", publication_type="OTHER")
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
