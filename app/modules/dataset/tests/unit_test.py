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
