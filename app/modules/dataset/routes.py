import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile

from flask import (
    Response,
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import CSVFile, DataSet, DSDownloadRecord, DSMetaData
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            # Convert form errors to readable message
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            error_message = "; ".join(error_messages)
            return jsonify({"message": error_message}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_csv_files(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each CSV file (one CSV file = one request to Zenodo)
                for csv_file in dataset.csv_files:
                    zenodo_service.upload_file(dataset, deposition_id, csv_file)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload CSV files in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".csv"):
        return jsonify({"message": "No valid file"}), 400

    is_valid, error_message = DataSetService.validate_csv_content(file)
    if not is_valid:
        return jsonify({"message": error_message}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){extension}")):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "CSV uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
@dataset_bp.route("/dataset/download/<int:dataset_id>/<int:version_id>", methods=["GET"])
def download_dataset(dataset_id, version_id=None):
    dataset = dataset_service.get_or_404(dataset_id)

    # If a specific version is requested, use that; otherwise use the current dataset
    if version_id is not None:
        download_dataset_obj = dataset_service.get_or_404(version_id)
        # Verify that the version belongs to this dataset chain
        all_versions = dataset.get_all_versions()
        if download_dataset_obj not in all_versions:
            abort(404)
    else:
        download_dataset_obj = dataset

    file_path = f"uploads/user_{download_dataset_obj.user_id}/dataset_{download_dataset_obj.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}_v{download_dataset_obj.version}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())  # Generate a new unique identifier if it does not exist
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}_v{download_dataset_obj.version}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}_v{download_dataset_obj.version}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Check if the download record already exists for this cookie
    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie,
    ).first()

    if not existing_record:
        # Record the download in your database
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )
    dataset.ds_meta_data.downloads += 1
    dataset_service.update_dsmetadata(dataset.ds_meta_data_id)
    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI      - código HTML y Markdown embebibles
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Get related datasets
    related_datasets = dataset_service.get_related_datasets(dataset.id)

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(
        render_template("dataset/view_dataset.html", dataset=dataset, related_datasets=related_datasets)
    )
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    if current_user.is_authenticated:
        dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)
    else:
        # Allow anonymous users to view unsynchronized datasets
        dataset = (
            DataSet.query.filter_by(id=dataset_id).join(DSMetaData).filter(DSMetaData.dataset_doi.is_(None)).first()
        )

    if not dataset:
        abort(404)

    related_datasets = dataset_service.get_related_datasets(dataset.id)

    return render_template("dataset/view_dataset.html", dataset=dataset, related_datasets=related_datasets)


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


@dataset_bp.route("/dataset/<int:dataset_id>/badge.svg")
def dataset_badge(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    dataset_name = dataset.ds_meta_data.title
    downloads = dataset.ds_meta_data.downloads

    label = xml_escape(dataset_name)
    value = f"{downloads:,}"

    left_width = max(90, len(label) * 7 + 30)
    right_width = max(70, len(value) * 8 + 26)
    height = 28
    total_width = left_width + right_width

    svg = f"""\
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label} downloads">
    <defs>
        <linearGradient id="badge-glow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0ea5e9"/>
            <stop offset="100%" stop-color="#14b8a6"/>
        </linearGradient>
        <linearGradient id="badge-fill" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#111827"/>
            <stop offset="100%" stop-color="#0b1220"/>
        </linearGradient>
    </defs>

    <rect width="{total_width}" height="{height}" rx="8" fill="url(#badge-fill)" stroke="#0ea5e9" stroke-width="1"/>
    <rect x="{left_width}" width="{right_width}" height="{height}" rx="8" fill="url(#badge-glow)"/>
    <line x1="{left_width}" y1="1" x2="{left_width}" y2="{height - 1}" stroke="#0ea5e9" stroke-opacity="0.35"/>

    <g fill="#e2e8f0" text-anchor="middle" font-family="Segoe UI, Ubuntu, Helvetica, sans-serif" font-size="12" font-weight="600">
        <text x="{left_width/2}" y="{height/2 + 4}">{label}</text>
        <text x="{left_width + right_width/2}" y="{height/2 + 4}" fill="#0b1220">{value}</text>
    </g>
</svg>
"""

    response = Response(svg, mimetype="image/svg+xml")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@dataset_bp.route("/dataset/<int:dataset_id>/badge/<badge_type>")
def copyable_badge(dataset_id, badge_type):
    base_url = request.host_url.rstrip("/")
    svg_url = f"{base_url}/dataset/{dataset_id}/badge.svg"

    if badge_type == "md":
        return f"![Dataset downloads]({svg_url})", 200, {"Content-Type": "text/plain; charset=utf-8"}

    if badge_type == "html":
        return f'<img src="{svg_url}" alt="Dataset downloads">', 200, {"Content-Type": "text/plain; charset=utf-8"}

    return "Invalid badge type", 400


@dataset_bp.route("/csvfile/download/<int:file_id>", methods=["GET"])
def download_csv_file(file_id):

    csv_file = CSVFile.query.get_or_404(file_id)
    dataset = csv_file.data_set

    file_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", csv_file.name)

    # Record download
    user_id = current_user.id if current_user.is_authenticated else None
    DSDownloadRecordService().create(
        user_id=user_id,
        dataset_id=dataset.id,
        download_date=datetime.now(timezone.utc),
        download_cookie=request.cookies.get("download_cookie", str(uuid.uuid4())),
    )
    dataset.ds_meta_data.downloads += 1
    dataset_service.update_dsmetadata(dataset.ds_meta_data_id)

    return send_file(f"/app/{file_path}", as_attachment=True)


@dataset_bp.route("/csvfile/view/<int:file_id>", methods=["GET"])
def view_csv_file(file_id):

    csv_file = CSVFile.query.get_or_404(file_id)
    dataset = csv_file.data_set

    file_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", csv_file.name)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"content": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dataset_bp.route("/csvfile/validate/<int:file_id>", methods=["GET"])
def validate_csv_file(file_id):
    from app.modules.dataset.models import CSVFile

    csv_file = CSVFile.query.get_or_404(file_id)
    dataset = csv_file.data_set

    file_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", csv_file.name)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_contents = f.readlines()

        if not file_contents:
            return jsonify({"errors": ["CSV file is empty"]}), 400

        # Check for valid header
        if len(file_contents) < 2:
            return jsonify({"errors": ["CSV must contain a header and at least one data row"]}), 400

        return jsonify({"message": "Valid CSV file"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dataset_bp.route("/dataset/<int:dataset_id>/compare", methods=["GET"])
def compare_versions(dataset_id):
    """
    Compare the current dataset version with a specified version or the previous version by default.
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    compare_version_id = request.args.get("version_id", type=int)
    compare_version = None

    if compare_version_id:
        compare_version = dataset_service.get_by_id(compare_version_id)
        if not compare_version:
            return jsonify({"error": "Version to compare not found"}), 404

    comparison_result = dataset.compare_with_version(compare_version)

    return jsonify(comparison_result), 200


@dataset_bp.route("/dataset/<int:dataset_id>/compare_metadata", methods=["GET"])
def compare_metadata_versions(dataset_id):
    """
    Compare the current dataset version's metadata with a specified version or the previous version by default.
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    compare_version_id = request.args.get("version_id", type=int)
    compare_version = None

    if compare_version_id:
        compare_version = dataset_service.get_by_id(compare_version_id)
        if not compare_version:
            return jsonify({"error": "Version to compare not found"}), 404

    comparison_result = dataset.compare_metadata_with_version(compare_version)
    return jsonify(comparison_result), 200


@dataset_bp.route("/dataset/<int:dataset_id>/compare/diff/<file_name>", methods=["GET"])
def get_file_diff(dataset_id, file_name):
    """
    Get a detailed diff of a specific file between two versions.
    Query parameter: version_id (optional) - the version to compare with
    """
    from app.modules.dataset.models import CSVFile
    from app.modules.dataset.services import DiffService

    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    compare_version_id = request.args.get("version_id", type=int)
    compare_version = dataset.previous_version

    if compare_version_id:
        compare_version = dataset_service.get_by_id(compare_version_id)
        if not compare_version:
            return jsonify({"error": "Version to compare not found"}), 404

    if not compare_version:
        return jsonify({"error": "No previous version to compare"}), 404

    # Find the file in both versions
    current_file = CSVFile.query.filter_by(name=file_name, dataset_id=dataset.id).first()
    previous_file = CSVFile.query.filter_by(name=file_name, dataset_id=compare_version.id).first()

    if not current_file or not previous_file:
        return jsonify({"error": "File not found in one or both versions"}), 404

    # Get file paths
    working_dir = os.getenv("WORKING_DIR", "")
    current_path = os.path.join(working_dir, "uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", file_name)
    previous_path = os.path.join(
        working_dir,
        "uploads",
        f"user_{compare_version.user_id}",
        f"dataset_{compare_version.id}",
        file_name,
    )

    try:
        diff_result = DiffService.get_file_diff(previous_path, current_path)
        return jsonify(diff_result), 200
    except Exception as e:
        logger.exception(f"Error generating diff for file {file_name}: {e}")
        return jsonify({"error": str(e)}), 500


@dataset_bp.route("/dataset/<int:dataset_id>/edit", methods=["GET"])
@login_required
def edit_dataset(dataset_id):
    """
    Edit a dataset - only the owner can edit it.
    Allows uploading new files or deleting existing ones to create a new version.
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        abort(404)

    # Only the owner can edit the dataset
    if current_user.id != dataset.user_id:
        abort(403)

    form = DataSetForm()

    return render_template("dataset/edit_dataset.html", dataset=dataset, form=form)


@dataset_bp.route("/dataset/<int:dataset_id>/update", methods=["POST"])
@login_required
def update_dataset(dataset_id):
    """
    Update a dataset by uploading new files, removing files, or updating metadata.
    Creates a new version and maintains previous version link.
    """
    dataset = dataset_service.get_by_id(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    # Only the owner can edit the dataset
    if current_user.id != dataset.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    # Get the list of files to delete and metadata changes
    data = request.get_json() or {}
    files_to_delete = data.get("files_to_delete", [])
    metadata_changes = data.get("metadata", None)

    try:
        # Create a new version with optional metadata changes
        new_version = dataset_service.create_new_version(dataset, files_to_delete, current_user, metadata_changes)

        # Move new CSV files from temp folder to the new version's directory
        dataset_service.move_csv_files(new_version)

        return (
            jsonify(
                {
                    "message": "Dataset updated successfully",
                    "new_version_id": new_version.id,
                    "version": new_version.version,
                }
            ),
            200,
        )
    except Exception as e:
        logger.exception(f"Exception updating dataset: {e}")
        return jsonify({"error": str(e)}), 500
