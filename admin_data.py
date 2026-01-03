from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
import pandas as pd
from functools import wraps
from data_store import load_data, save_data, clear_cache

admin_data_bp = Blueprint("admin_data", __name__, url_prefix="/admin")

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Akses admin diperlukan", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return wrapper


# =====================
# HALAMAN DATA ADMIN
# =====================
@admin_data_bp.route("/data")
@admin_required
def data_table():
    df = load_data().copy()

    for c in ["No", "no"]:
        if c in df.columns:
            df.drop(columns=[c], inplace=True)

    df.insert(0, "no", range(1, len(df) + 1))
    return render_template("data_admin.html", columns=df.columns.tolist())


# =====================
# API DATATABLES (FAST)
# =====================
@admin_data_bp.route("/data/json")
@admin_required
def api():
    df = load_data().copy()

    for c in ["No", "no"]:
        if c in df.columns:
            df.drop(columns=[c], inplace=True)

    df.insert(0, "no", range(1, len(df) + 1))

    draw = int(request.args.get("draw", 1))
    start = int(request.args.get("start", 0))
    length = int(request.args.get("length", 25))
    search = request.args.get("search[value]", "").strip()

    if search:
        mask = df.astype(str).apply(
            lambda x: x.str.contains(search, case=False, na=False)
        ).any(axis=1)
        filtered = df[mask]
    else:
        filtered = df

    page = filtered.iloc[start:start + length]

    data = []
    for _, row in page.iterrows():
        r = row.to_dict()
        r["aksi"] = f"""
            <a href="{url_for('admin_data.edit_data', no=row['no'])}"
               class="btn btn-warning btn-sm mr-1">
               ✏️
            </a>
            <a href="{url_for('admin_data.hapus_data', no=row['no'])}"
               class="btn btn-danger btn-sm delete-btn">
               🗑️
            </a>
        """
        data.append({k: str(v) for k, v in r.items()})

    return jsonify({
        "draw": draw,
        "recordsTotal": len(df),
        "recordsFiltered": len(filtered),
        "data": data
    })


# =====================
# EDIT & HAPUS
# =====================
@admin_data_bp.route("/edit/<int:no>", methods=["GET", "POST"])
@admin_required
def edit_data(no):
    df = load_data()

    if no < 1 or no > len(df):
        flash("Data tidak ditemukan", "danger")
        return redirect(url_for("admin_data.data_table"))

    if request.method == "POST":
        for col in df.columns:
            df.at[no - 1, col] = request.form.get(col, "")
        save_data(df)
        clear_cache()
        flash("Data berhasil diperbarui", "success")
        return redirect(url_for("admin_data.data_table"))

    return render_template("data_edit.html", data=df.iloc[no - 1].to_dict(), no=no)


@admin_data_bp.route("/hapus/<int:no>")
@admin_required
def hapus_data(no):
    df = load_data()

    if no < 1 or no > len(df):
        flash("Data tidak ditemukan", "danger")
        return redirect(url_for("admin_data.data_table"))

    df = df.drop(df.index[no - 1]).reset_index(drop=True)
    save_data(df)
    clear_cache()
    flash("Data berhasil dihapus", "success")
    return redirect(url_for("admin_data.data_table"))
