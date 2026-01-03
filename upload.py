from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
from data_store import load_data, save_data, clear_cache

upload_bp = Blueprint("upload", __name__)
DATA_FILE = "data.xlsx"


@upload_bp.route("/upload", methods=["GET", "POST"])
def upload_excel():
    if session.get("role") != "admin":
        flash("Hanya admin yang bisa mengakses halaman ini.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        file = request.files.get("file")
        mode = request.form.get("mode")

        if not file or not file.filename.endswith(".xlsx"):
            flash("File harus .xlsx", "danger")
            return redirect(request.url)

        try:
            # ===== BACA DATA BARU =====
            df_new = pd.read_excel(file, dtype=str, engine="openpyxl")
            df_new.fillna("", inplace=True)

            # hapus kolom no jika ada
            for c in ["no", "No"]:
                if c in df_new.columns:
                    df_new.drop(columns=[c], inplace=True)

            # ===== MODE TAMBAH DATA =====
            if mode == "append" and os.path.exists(DATA_FILE):
                df_old = load_data()

                for c in ["no", "No"]:
                    if c in df_old.columns:
                        df_old.drop(columns=[c], inplace=True)

                df_final = pd.concat([df_old, df_new], ignore_index=True)
                flash("✅ Data berhasil ditambah", "success")

            # ===== MODE UPLOAD ULANG =====
            else:
                df_final = df_new
                flash("✅ Data berhasil disimpan (Upload Ulang)", "success")

            # ===== SIMPAN SEKALI SAJA =====
            save_data(df_final)
            clear_cache()

        except Exception as e:
            flash(f"❌ Gagal upload: {str(e)}", "danger")
            return redirect(request.url)

        return redirect(url_for("upload.upload_excel"))

    return render_template("upload.html")
