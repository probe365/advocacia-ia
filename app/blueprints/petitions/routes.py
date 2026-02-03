# app/blueprints/petitions/routes.py
from flask import Blueprint, request, render_template, g
from flask_login import login_required, current_user
from app.services.petition_service import PetitionService

petitions_bp = Blueprint("petitions", __name__, url_prefix="/petitions")
service = PetitionService()

@petitions_bp.route("/create", methods=["POST"])
@login_required
def create_petition():
    process_id = request.form.get("process_id")
    petition_type = request.form.get("petition_type")

    service.create_petition(
        tenant_id=g.tenant_id,
        user_id=current_user.id,
        process_id=process_id,
        petition_type=petition_type,
    )

    petitions = service.list_by_process(g.tenant_id, process_id)
    return render_template(
        "petitions/_list.html",
        petitions=petitions,
        process_id=process_id,
    )

@petitions_bp.route("/partial/list")
@login_required
def list_petitions():
    process_id = request.args.get("process_id")
    petitions = service.list_by_process(g.tenant_id, process_id)

    return render_template(
        "petitions/_list.html",
        petitions=petitions,
        process_id=process_id,
    )

@petitions_bp.route("/<int:petition_id>/partial/editor")
@login_required
def petition_editor(petition_id):
    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)

    return render_template(
        "petitions/_editor.html",
        petition=petition,
        versions=versions,
    )

@petitions_bp.route("/<int:petition_id>/render", methods=["POST"])
@login_required
def render_petition(petition_id):
    service.render_from_template(
        tenant_id=g.tenant_id,
        user_id=current_user.id,
        petition_id=petition_id,
    )

    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)

    return render_template(
        "petitions/_editor.html",
        petition=petition,
        versions=versions,
    )
