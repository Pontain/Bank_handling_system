from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_security.decorators import auth_required, roles_required
from flask_login import current_user
from services.staff_service import StaffService
from models.model import Role, Employee
from database import db
from sqlalchemy import select


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
@auth_required()
@roles_required("ADMIN")
def get_all_staff():
    # Pagination
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    # Sorting (matchar StaffService.SORT_COLUMNS keys)
    sort_by = request.args.get("sort_by", default="id", type=str)
    sort_order = request.args.get("sort_order", default="asc", type=str)

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

    # Lista alla roller (för dropdowns/checkboxar i UI om du vill)
    roles = db.session.execute(select(Role).order_by(Role.name.asc())).scalars().all()

    return render_template(
        "admin/admin.html",
        staff=pagination.items,
        pagination=pagination,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        q=q,
        include_inactive=include_inactive,
        roles=roles,
    )


@admin_bp.route("/by-id", methods=["GET"])
@auth_required()
@roles_required("ADMIN")
def by_id():
    staff_id = request.args.get("id", type=int)

    if not staff_id:
        flash("Invalid staff id", "danger")
        return redirect(url_for("admin.get_all_staff"))

    return redirect(url_for("admin.get_one", id=staff_id))


@admin_bp.route("/<int:id>", methods=["GET"])
@auth_required()
@roles_required("ADMIN")
def get_one(id: int):
    user = StaffService.get_by_id(id)
    if not user:
        abort(404)

    all_roles = db.session.execute(select(Role).order_by(Role.name.asc())).scalars().all()

    return render_template(
        "admin/staff.html",
        user=user,
        all_roles=all_roles,
    )


@admin_bp.route("/create", methods=["GET", "POST"])
@auth_required()
@roles_required("ADMIN")
def create_staff():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # checkboxar med role names, t.ex. ADMIN / CASHIER
        role_names = [r.strip().upper() for r in request.form.getlist("roles") if r.strip()]

        if not email or not username or not password:
            flash("Email, username and password are required", "danger")
            return redirect(url_for("admin.create_staff"))

        # (valfritt) enkel guard så man inte råkar skapa dubletter
        if StaffService.get_by_email(email):
            flash("Email already exists", "danger")
            return redirect(url_for("admin.create_staff"))

        if StaffService.get_by_username(username):
            flash("Username already exists", "danger")
            return redirect(url_for("admin.create_staff"))

        StaffService.create_user(
            email=email,
            username=username,
            password_plain=password,
            role_names=role_names,
            active=True,
        )

        flash("Staff user created", "success")
        return redirect(url_for("admin.get_all_staff"))

    # För GET: skicka roller till formuläret
    roles = db.session.execute(select(Role).order_by(Role.name.asc())).scalars().all()
    return render_template("admin/create_staff.html", roles=roles)


@admin_bp.route("/<int:id>/set-active", methods=["POST"])
@auth_required()
@roles_required("ADMIN")
def set_active(id: int):
    is_active = request.form.get("is_active") == "1"

    if current_user.id == id and not is_active:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.get_one", id=id))

    StaffService.set_active(id, is_active)

    flash("Staff status updated", "success")
    return redirect(url_for("admin.get_one", id=id))


@admin_bp.route("/<int:id>/roles/add", methods=["POST"])
@auth_required()
@roles_required("ADMIN")
def add_role(id: int):
    role_name = request.form.get("role", "").strip().upper()

    if not role_name:
        flash("No role provided.", "danger")
        return redirect(url_for("admin.get_one", id=id))

    StaffService.add_role(id, role_name)
    flash(f"Role added: {role_name}", "success")
    return redirect(url_for("admin.get_one", id=id))


@admin_bp.route("/<int:id>/roles/remove", methods=["POST"])
@auth_required()
@roles_required("ADMIN")
def remove_role(id: int):
    role_name = request.form.get("role", "").strip().upper()

    if current_user.id == id and role_name == "ADMIN":
        flash("You cannot remove the ADMIN role from your own account.", "danger")
        return redirect(url_for("admin.get_one", id=id))

    if not role_name:
        flash("No role provided.", "danger")
        return redirect(url_for("admin.get_one", id=id))

    StaffService.remove_role(id, role_name)
    flash(f"Role removed: {role_name}", "success")
    return redirect(url_for("admin.get_one", id=id))


@admin_bp.post("/<int:id>/delete")
@auth_required()
@roles_required("ADMIN")
def delete_employee(id: int):

    if current_user.id == id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.get_one", id=id))

    employee = StaffService.get_by_id_including_deleted(id)

    if not employee:
        abort(404)

    employee.soft_delete()
    db.session.commit()

    flash("Employee deleted", "success")
    return redirect(url_for("admin.get_all_staff"))


@admin_bp.post("/<int:id>/restore")
@auth_required()
@roles_required("ADMIN")
def restore_employee(id: int):
    employee = StaffService.get_by_id_including_deleted(id)

    if not employee:
        abort(404)

    employee.is_deleted = False
    employee.deleted_at = None
    employee.active = False  # kräver manuell aktivering

    db.session.commit()

    flash("Employee restored (inactive)", "success")
    return redirect(url_for("admin.get_one", id=id))
