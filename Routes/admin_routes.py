from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from services.staff_service import StaffService
from models.model import StaffRole

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
def get_all_staff():
    # Pagination
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    # Sorting
    sort_by = request.args.get("sort_by", default="Id")
    sort_order = request.args.get("sort_order", default="asc")

    # Search
    q = request.args.get("q", default="", type=str)

    # Visa inaktiva?
    include_inactive = request.args.get("include_inactive") in ("1", "true", "on")

    pagination = StaffService.get_paginated(
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        q=q,
        include_inactive=include_inactive,
    )

    return render_template(
        "/admin/admin.html",
        staff=pagination.items,
        pagination=pagination,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        q=q,
        include_inactive=include_inactive,
    )

@admin_bp.route("/by-id", methods=["GET"])
def by_id():
    staff_id = request.args.get("id", type=int)

    if not staff_id:
        flash("Invalid staff id", "danger")
        return redirect(url_for("admin.get_all_staff"))

    return redirect(url_for("admin.get_one", id=staff_id))


@admin_bp.route("/<int:id>", methods=["GET"])
def get_one(id: int):
    user = StaffService.get_by_id(id)
    if not user:
        abort(404)

    return render_template(
        "/admin/staff.html",
        user=user
    )

@admin_bp.route("/create", methods=["GET", "POST"])
def create_staff():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        roles_raw = request.form.getlist("roles")  # checkboxar

        if not username:
            flash("Username is required", "danger")
            return redirect(url_for("admin.create_staff"))

        # konvertera strängar → enums
        roles = []
        for r in roles_raw:
            try:
                roles.append(StaffRole(r))
            except ValueError:
                pass

        StaffService.create_user(username, roles=roles)

        flash("Staff user created", "success")
        return redirect(url_for("admin.get_all_staff"))

    return render_template("/admin/create_staff.html")


@admin_bp.route("/<int:id>/set-active", methods=["POST"])
def set_active(id: int):
    is_active = request.form.get("is_active") == "1"
    StaffService.set_active(id, is_active)

    flash("Staff status updated", "success")
    return redirect(url_for("admin.get_one", id=id))

@admin_bp.route("/<int:id>/roles/add", methods=["POST"])
def add_role(id: int):
    role_str = request.form.get("role", "").strip().upper()

    if not role_str:
        flash("No role provided.", "danger")
        return redirect(url_for("admin.get_one", id=id))

    # Konvertera sträng -> enum
    try:
        role = StaffRole(role_str)
    except ValueError:
        flash(f"Invalid role: {role_str}", "danger")
        return redirect(url_for("admin.get_one", id=id))

    StaffService.add_role(id, role)
    flash(f"Role added: {role.value}", "success")
    return redirect(url_for("admin.get_one", id=id))

@admin_bp.route("/<int:id>/roles/remove", methods=["POST"])
def remove_role(id: int):
    role_str = request.form.get("role", "").strip().upper()

    if not role_str:
        flash("No role provided.", "danger")
        return redirect(url_for("admin.get_one", id=id))

    try:
        role = StaffRole(role_str)
    except ValueError:
        flash(f"Invalid role: {role_str}", "danger")
        return redirect(url_for("admin.get_one", id=id))

    StaffService.remove_role(id, role)
    flash(f"Role removed: {role.value}", "success")
    return redirect(url_for("admin.get_one", id=id))
