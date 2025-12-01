import pytest

from app.modules.dataset.models import DataSet, DSMetaData


@pytest.fixture(scope="module")
def test_dataset_id(test_client):
    from app import db

    with test_client.application.app_context():
        ds_meta = DSMetaData(title="Test Dataset", description="This is a test dataset", publication_type="NONE")
        db.session.add(ds_meta)
        db.session.commit()

        dataset = DataSet(user_id=1, ds_meta_data_id=ds_meta.id)
        db.session.add(dataset)
        db.session.commit()

        dataset_id = dataset.id

    yield dataset_id

    # Cleanup
    with test_client.application.app_context():
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
