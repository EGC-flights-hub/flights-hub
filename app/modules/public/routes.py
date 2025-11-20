import logging

from flask import render_template

from app.modules.dataset.services import DataSetService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()

    # Statistics: total datasets
    datasets_counter = dataset_service.count_synchronized_datasets()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        trending_datasets=dataset_service.trending_datasets(),
        datasets_counter=datasets_counter,
        feature_models_counter=feature_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_feature_model_downloads=total_feature_model_downloads,
        total_dataset_views=total_dataset_views,
        total_feature_model_views=total_feature_model_views,
    )
