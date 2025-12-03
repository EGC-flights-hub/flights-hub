import pytest
from app.modules.dataset.services import DataSetService
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app import db


@pytest.fixture(scope="module")
def dataset_service():
    return DataSetService()


def test_recommendation_logic(test_client):
    service = DataSetService()

    from app.modules.auth.models import User
    user = User.query.filter_by(email='test_rec@test.com').first()
    if not user:
        user = User(email='test_rec@test.com', password='password123')
        db.session.add(user)
        db.session.commit()

    target_meta = DSMetaData(
        title="Target Dataset", description="Target",
        publication_type=PublicationType.OTHER,
        tags="auto, ai", deposition_id=1001, dataset_doi="10.1234/target"
    )
    target_ds = DataSet(user_id=user.id, ds_meta_data=target_meta)
    db.session.add(target_ds)

    meta_a = DSMetaData(
        title="Dataset A (High)", description="Desc A",
        publication_type=PublicationType.OTHER,
        tags="auto, ai, robot", deposition_id=1002, dataset_doi="10.1234/ds_a",
        downloads=100
    )
    ds_a = DataSet(user_id=user.id, ds_meta_data=meta_a)
    db.session.add(ds_a)

    meta_b = DSMetaData(
        title="Dataset B (Med)", description="Desc B",
        publication_type=PublicationType.OTHER,
        tags="auto, food", deposition_id=1003, dataset_doi="10.1234/ds_b",
        downloads=0
    )
    ds_b = DataSet(user_id=user.id, ds_meta_data=meta_b)
    db.session.add(ds_b)

    meta_c = DSMetaData(
        title="Dataset C (None)", description="Desc C",
        publication_type=PublicationType.OTHER,
        tags="fruit, water", deposition_id=1004, dataset_doi="10.1234/ds_c"
    )
    ds_c = DataSet(user_id=user.id, ds_meta_data=meta_c)
    db.session.add(ds_c)

    db.session.commit()

    recommendations = service.get_related_datasets(target_ds.id)

    assert len(recommendations) >= 2

    ids_found = [d.id for d in recommendations]
    assert ds_c.id not in ids_found

    assert recommendations[0].id == ds_a.id
    assert recommendations[1].id == ds_b.id

    db.session.delete(target_ds)
    db.session.delete(ds_a)
    db.session.delete(ds_b)
    db.session.delete(ds_c)
    db.session.delete(user)
    db.session.commit()
