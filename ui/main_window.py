"""
Module: ui/main_window.py
Description: Full-featured desktop GUI in Tkinter for AutoDataPrep with 7 modular sections,
             multi-threaded execution, embedded Matplotlib visualizations, and interactive tables.
"""

import os
import sys
import threading
import webbrowser
from typing import Dict, List, Any, Optional
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.data_loader import load_dataset, detect_csv_parameters, format_bytes, SUPPORTED_EXTENSIONS
from core.data_analyzer import DataAnalyzer, VariableType
from core.data_cleaner import DataCleaner
from core.feature_transformer import FeatureTransformer
from core.ml_preprocessor import MLPreprocessor, MLTaskType
from core.export_manager import ExportManager
from core.report_generator import ReportGenerator


class MainWindow:
    """Main Application Controller and Tkinter UI."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AutoDataPrep — Assistant Intelligent de Préparation des Données ML")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)

        # Application State
        self.file_path: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.df_raw: Optional[pd.DataFrame] = None
        self.cleaner: Optional[DataCleaner] = None
        self.analysis_results: Dict[str, Any] = {}
        self.transformer: Optional[FeatureTransformer] = None
        self.ml_prep_results: Optional[Dict[str, Any]] = None

        # Pagination State
        self.preview_page = 0
        self.preview_page_size = 50

        # Output managers
        self.export_manager = ExportManager(output_dir="exports")
        self.report_generator = ReportGenerator(output_dir="reports")

        # Setup Theme and Styles
        self._setup_styles()

        # Build Layout
        self._build_main_layout()

    def _setup_styles(self):
        """Configure modern ttk styles."""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Colors
        self.COLOR_PRIMARY = "#2563eb"
        self.COLOR_SIDEBAR = "#0f172a"
        self.COLOR_SIDEBAR_HOVER = "#1e293b"
        self.COLOR_SIDEBAR_ACTIVE = "#3b82f6"
        self.COLOR_BG = "#f8fafc"
        self.COLOR_CARD = "#ffffff"
        self.COLOR_TEXT = "#1e293b"

        self.root.configure(bg=self.COLOR_BG)

        self.style.configure(".", background=self.COLOR_BG, foreground=self.COLOR_TEXT, font=("Segoe UI", 10))
        self.style.configure("Sidebar.TFrame", background=self.COLOR_SIDEBAR)
        self.style.configure("Card.TFrame", background=self.COLOR_CARD, relief="solid", borderwidth=1)
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), background=self.COLOR_BG, foreground="#0f172a")
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 10, "italic"), background=self.COLOR_BG, foreground="#64748b")
        self.style.configure("KpiTitle.TLabel", font=("Segoe UI", 8, "bold"), foreground="#64748b", background=self.COLOR_CARD)
        self.style.configure("KpiVal.TLabel", font=("Segoe UI", 13, "bold"), foreground="#0f172a", background=self.COLOR_CARD)

        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=self.COLOR_PRIMARY, foreground="white")
        self.style.map("Primary.TButton", background=[("active", "#1d4ed8")])

        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=26, background="white")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e2e8f0")

    def _build_main_layout(self):
        """Builds top-level container: sidebar, content area, and status bar."""
        # 1. Main Horizontal Split: Sidebar + Content
        self.main_container = tk.Frame(self.root, bg=self.COLOR_BG)
        self.main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Sidebar
        self.sidebar_frame = tk.Frame(self.main_container, bg=self.COLOR_SIDEBAR, width=230)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # Content Area
        self.content_frame = tk.Frame(self.main_container, bg=self.COLOR_BG)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 2. Bottom Status Bar
        self.status_bar = tk.Frame(self.root, bg="#e2e8f0", height=28)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)

        self.lbl_status = tk.Label(self.status_bar, text="Prêt — Aucun dataset chargé", bg="#e2e8f0", fg="#334155", font=("Segoe UI", 9), anchor="w")
        self.lbl_status.pack(side=tk.LEFT, padx=12, fill=tk.X, expand=True)

        self.lbl_dataset_info = tk.Label(self.status_bar, text="", bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9, "bold"))
        self.lbl_dataset_info.pack(side=tk.RIGHT, padx=12)

        self.progress_bar = ttk.Progressbar(self.status_bar, mode="indeterminate", length=140)

        # Build Sidebar Navigation
        self._build_sidebar()

        # Build View Sections
        self.views: Dict[str, tk.Frame] = {}
        self._build_views()

        # Show Section 1 by default
        self.switch_section("import")

    def _build_sidebar(self):
        """Constructs sidebar buttons with modern icons and labels."""
        # App Title in Sidebar
        title_frame = tk.Frame(self.sidebar_frame, bg=self.COLOR_SIDEBAR, height=65)
        title_frame.pack(fill=tk.X, pady=(15, 20), padx=15)
        lbl_logo = tk.Label(title_frame, text="⚡ AutoDataPrep", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg=self.COLOR_SIDEBAR)
        lbl_logo.pack(anchor="w")
        lbl_sub = tk.Label(title_frame, text="ML Data Prep Studio", font=("Segoe UI", 8), fg="#94a3b8", bg=self.COLOR_SIDEBAR)
        lbl_sub.pack(anchor="w")

        # Nav Buttons list
        self.nav_items = [
            ("import", "📁 1. Accueil & Import"),
            ("eda", "📊 2. Analyse Exploratoire"),
            ("audit", "🔍 3. Audit de Qualité"),
            ("cleaning", "🧹 4. Nettoyage"),
            ("transforms", "⚙️ 5. Transformations"),
            ("ml", "🤖 6. Configuration ML"),
            ("export", "💾 7. Résultats & Export")
        ]

        self.nav_buttons: Dict[str, tk.Button] = {}
        for key, label in self.nav_items:
            btn = tk.Button(
                self.sidebar_frame,
                text=f"  {label}",
                font=("Segoe UI", 9, "bold"),
                fg="#cbd5e1",
                bg=self.COLOR_SIDEBAR,
                activebackground=self.COLOR_SIDEBAR_HOVER,
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                anchor="w",
                padx=15,
                pady=10,
                command=lambda k=key: self.switch_section(k)
            )
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[key] = btn

    def switch_section(self, section_key: str):
        """Switches active visible view."""
        for key, frame in self.views.items():
            frame.pack_forget()

        for key, btn in self.nav_buttons.items():
            if key == section_key:
                btn.configure(bg=self.COLOR_SIDEBAR_ACTIVE, fg="#ffffff")
            else:
                btn.configure(bg=self.COLOR_SIDEBAR, fg="#cbd5e1")

        if section_key in self.views:
            self.views[section_key].pack(fill=tk.BOTH, expand=True)

        # Trigger on-show refresh hooks
        if section_key == "eda":
            self._refresh_eda_view()
        elif section_key == "audit":
            self._refresh_audit_view()
        elif section_key == "cleaning":
            self._refresh_cleaning_view()
        elif section_key == "transforms":
            self._refresh_transforms_view()
        elif section_key == "ml":
            self._refresh_ml_view()
        elif section_key == "export":
            self._refresh_export_view()

    def set_status(self, text: str, is_busy: bool = False):
        """Updates status text and toggles progress bar."""
        self.lbl_status.config(text=text)
        if is_busy:
            self.progress_bar.pack(side=tk.RIGHT, padx=10)
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

    def run_async(self, worker_func, on_success=None, on_error=None, busy_msg="Traitement en cours..."):
        """Executes long-running operations in background thread to prevent UI freezing."""
        self.set_status(busy_msg, is_busy=True)

        def run():
            try:
                res = worker_func()
                self.root.after(0, lambda: self._handle_async_success(res, on_success))
            except Exception as e:
                self.root.after(0, lambda: self._handle_async_error(e, on_error))

        threading.Thread(target=run, daemon=True).start()

    def _handle_async_success(self, result, callback):
        self.set_status("Prêt")
        if callback:
            callback(result)

    def _handle_async_error(self, error, callback):
        self.set_status("Erreur lors de l'opération")
        if callback:
            callback(error)
        else:
            messagebox.showerror("Erreur", str(error))

    # =========================================================================
    # VIEW BUILDERS
    # =========================================================================

    def _build_views(self):
        """Initializes all 7 views."""
        self.views["import"] = self._build_import_view()
        self.views["eda"] = self._build_eda_view()
        self.views["audit"] = self._build_audit_view()
        self.views["cleaning"] = self._build_cleaning_view()
        self.views["transforms"] = self._build_transforms_view()
        self.views["ml"] = self._build_ml_view()
        self.views["export"] = self._build_export_view()

    # -------------------------------------------------------------------------
    # 1. ACCUEIL & IMPORTATION
    # -------------------------------------------------------------------------
    def _build_import_view(self) -> tk.Frame:
        view = tk.Frame(self.content_frame, bg=self.COLOR_BG, padx=25, pady=20)

        # Header
        top_bar = tk.Frame(view, bg=self.COLOR_BG)
        top_bar.pack(fill=tk.X, pady=(0, 15))
        lbl_h = ttk.Label(top_bar, text="📁 Importation & Gestion du Dataset", style="Header.TLabel")
        lbl_h.pack(side=tk.LEFT)

        btn_box = tk.Frame(top_bar, bg=self.COLOR_BG)
        btn_box.pack(side=tk.RIGHT)

        btn_import = tk.Button(
            btn_box, text="📂 Charger un fichier...", bg=self.COLOR_PRIMARY, fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6, command=self._action_browse_file
        )
        btn_import.pack(side=tk.LEFT, padx=6)

        btn_csv_opts = tk.Button(
            btn_box, text="⚙️ Paramètres CSV", bg="#e2e8f0", fg="#1e293b",
            font=("Segoe UI", 9), relief="flat", padx=10, pady=6, command=self._open_csv_settings_dialog
        )
        btn_csv_opts.pack(side=tk.LEFT)

        # KPI Metadata Cards
        self.kpi_frame = tk.Frame(view, bg=self.COLOR_BG)
        self.kpi_frame.pack(fill=tk.X, pady=(0, 15))

        self.kpi_widgets = {}
        kpis = [
            ("file_name", "FICHIER", "Aucun"),
            ("format", "FORMAT & ENCODAGE", "N/A"),
            ("dims", "DIMENSIONS", "0 × 0"),
            ("missing", "VALEURS MANQUANTES", "0 (0%)"),
            ("duplicates", "DOUBLONS", "0 (0%)"),
            ("memory", "MÉMOIRE", "0 Mo")
        ]
        for key, title, def_val in kpis:
            card = tk.Frame(self.kpi_frame, bg=self.COLOR_CARD, relief="solid", bd=1, padx=12, pady=10)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            t_lbl = ttk.Label(card, text=title, style="KpiTitle.TLabel")
            t_lbl.pack(anchor="w")
            v_lbl = ttk.Label(card, text=def_val, style="KpiVal.TLabel")
            v_lbl.pack(anchor="w", pady=(4, 0))
            self.kpi_widgets[key] = v_lbl

        # Preview Table Section
        table_container = tk.Frame(view, bg=self.COLOR_CARD, relief="solid", bd=1)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Table Control bar
        tbl_bar = tk.Frame(table_container, bg="#f1f5f9", padx=10, pady=6)
        tbl_bar.pack(fill=tk.X)
        ttk.Label(tbl_bar, text="Aperçu des données :", font=("Segoe UI", 9, "bold"), background="#f1f5f9").pack(side=tk.LEFT)

        self.lbl_page_info = ttk.Label(tbl_bar, text="Lignes 0 - 0", background="#f1f5f9", font=("Segoe UI", 9))
        self.lbl_page_info.pack(side=tk.RIGHT, padx=10)

        btn_next = tk.Button(tbl_bar, text="Suivant ▶", relief="flat", bg="#e2e8f0", command=lambda: self._paginate_preview(1))
        btn_next.pack(side=tk.RIGHT, padx=3)
        btn_prev = tk.Button(tbl_bar, text="◀ Précédent", relief="flat", bg="#e2e8f0", command=lambda: self._paginate_preview(-1))
        btn_prev.pack(side=tk.RIGHT, padx=3)

        # Treeview with scrollbars
        tbl_scroll_frame = tk.Frame(table_container, bg=self.COLOR_CARD)
        tbl_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_preview = ttk.Treeview(tbl_scroll_frame, show="headings", selectmode="browse")
        scroll_y = ttk.Scrollbar(tbl_scroll_frame, orient="vertical", command=self.tree_preview.yview)
        scroll_x = ttk.Scrollbar(tbl_scroll_frame, orient="horizontal", command=self.tree_preview.xview)
        self.tree_preview.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bottom Action Bar
        bottom_bar = tk.Frame(view, bg=self.COLOR_BG)
        bottom_bar.pack(fill=tk.X)

        self.btn_run_analysis = tk.Button(
            bottom_bar, text="🚀 Lancer l'Analyse Intelligente Complète",
            bg="#16a34a", fg="white", font=("Segoe UI", 11, "bold"),
            relief="flat", padx=20, pady=8, state=tk.DISABLED,
            command=self._action_run_full_analysis
        )
        self.btn_run_analysis.pack(side=tk.RIGHT)

        return view

    def _open_csv_settings_dialog(self):
        """Modal dialog to adjust CSV delimiter, encoding, and decimal separator."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Paramètres d'importation CSV")
        dlg.geometry("380x280")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Paramètres de lecture manuels", font=("Segoe UI", 11, "bold")).pack(pady=10)

        f = tk.Frame(dlg, padx=20)
        f.pack(fill=tk.BOTH, expand=True)

        tk.Label(f, text="Séparateur :").grid(row=0, column=0, sticky="w", pady=6)
        delim_var = tk.StringVar(value=self.metadata.get("delimiter", ","))
        cb_delim = ttk.Combobox(f, textvariable=delim_var, values=[",", ";", "\\t", "|"], width=10)
        cb_delim.grid(row=0, column=1, pady=6)

        tk.Label(f, text="Encodage :").grid(row=1, column=0, sticky="w", pady=6)
        enc_var = tk.StringVar(value=self.metadata.get("encoding", "utf-8"))
        cb_enc = ttk.Combobox(f, textvariable=enc_var, values=["utf-8", "utf-8-sig", "latin-1", "cp1252"], width=10)
        cb_enc.grid(row=1, column=1, pady=6)

        tk.Label(f, text="Séparateur décimal :").grid(row=2, column=0, sticky="w", pady=6)
        dec_var = tk.StringVar(value=self.metadata.get("decimal", "."))
        cb_dec = ttk.Combobox(f, textvariable=dec_var, values=[".", ","], width=10)
        cb_dec.grid(row=2, column=1, pady=6)

        def apply_csv_params():
            if not self.file_path:
                dlg.destroy()
                return
            sep = "\t" if delim_var.get() == "\\t" else delim_var.get()
            self._load_file_with_params(self.file_path, delimiter=sep, encoding=enc_var.get(), decimal=dec_var.get())
            dlg.destroy()

        tk.Button(dlg, text="Appliquer & Recharger", bg=self.COLOR_PRIMARY, fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, command=apply_csv_params).pack(pady=15)

    def _action_browse_file(self):
        """Opens file dialog and loads the selected dataset."""
        filetypes = [
            ("Fichiers compatibles", "*.csv;*.tsv;*.txt;*.xlsx;*.xls;*.json;*.parquet"),
            ("Fichiers CSV (*.csv)", "*.csv"),
            ("Fichiers Excel (*.xlsx, *.xls)", "*.xlsx;*.xls"),
            ("Fichiers JSON (*.json)", "*.json"),
            ("Tous les fichiers", "*.*")
        ]
        chosen = filedialog.askopenfilename(title="Sélectionner un dataset", filetypes=filetypes)
        if chosen:
            self._load_file_with_params(chosen)

    def _load_file_with_params(self, path: str, **kwargs):
        """Asynchronously loads dataset."""
        def worker():
            return load_dataset(path, **kwargs)

        def on_success(res):
            df, meta = res
            self.file_path = path
            self.metadata = meta
            self.df_raw = df.copy()
            self.cleaner = DataCleaner(df)
            self.transformer = FeatureTransformer(df)
            self.ml_prep_results = None

            # Update KPIs
            self.kpi_widgets["file_name"].config(text=meta["file_name"])
            self.kpi_widgets["format"].config(text=f"{meta['format']} ({meta['encoding']})")
            self.kpi_widgets["dims"].config(text=f"{meta['rows']} × {meta['cols']}")
            self.kpi_widgets["missing"].config(text=f"{meta['total_missing']} ({meta['missing_pct']}%)")
            self.kpi_widgets["duplicates"].config(text=f"{meta['duplicate_rows']} ({meta['duplicate_pct']}%)")
            self.kpi_widgets["memory"].config(text=meta["memory_formatted"])

            self.lbl_dataset_info.config(text=f"Dataset : {meta['rows']} lig. × {meta['cols']} col. ({meta['memory_formatted']})")
            self.btn_run_analysis.config(state=tk.NORMAL)

            # Populate preview table
            self.preview_page = 0
            self._update_preview_table(self.cleaner.df)

            # Auto-run analysis
            self._action_run_full_analysis()

        self.run_async(worker, on_success=on_success, busy_msg="Chargement du fichier...")

    def _update_preview_table(self, df: pd.DataFrame):
        """Displays paginated rows in the Treeview."""
        self.tree_preview.delete(*self.tree_preview.get_children())
        if df.empty:
            return

        cols = list(df.columns)
        self.tree_preview["columns"] = cols

        for col in cols:
            self.tree_preview.heading(col, text=col)
            self.tree_preview.column(col, width=120, minwidth=70, stretch=True)

        start = self.preview_page * self.preview_page_size
        end = min(start + self.preview_page_size, len(df))
        subset = df.iloc[start:end]

        for _, row in subset.iterrows():
            vals = [str(v) if pd.notna(v) else "<NA>" for v in row.values]
            self.tree_preview.insert("", "end", values=vals)

        self.lbl_page_info.config(text=f"Lignes {start + 1} - {end} sur {len(df)}")

    def _paginate_preview(self, direction: int):
        if self.cleaner is None:
            return
        df = self.cleaner.df
        total_pages = (len(df) - 1) // self.preview_page_size
        new_page = self.preview_page + direction
        if 0 <= new_page <= total_pages:
            self.preview_page = new_page
            self._update_preview_table(df)

    def _action_run_full_analysis(self):
        """Runs the semantic analyzer asynchronously."""
        if self.cleaner is None:
            return

        def worker():
            analyzer = DataAnalyzer()
            return analyzer.analyze_dataset(self.cleaner.df)

        def on_success(results):
            self.analysis_results = results
            messagebox.showinfo("Analyse terminée", "L'analyse intelligente du dataset a été effectuée avec succès !\nConsultez les sections EDA et Audit pour voir les résultats.")
            self.switch_section("eda")

        self.run_async(worker, on_success=on_success, busy_msg="Analyse sémantique et audit du dataset...")

    # -------------------------------------------------------------------------
    # 2. ANALYSE EXPLORATOIRE (EDA)
    # -------------------------------------------------------------------------
    def _build_eda_view(self) -> tk.Frame:
        view = tk.Frame(self.content_frame, bg=self.COLOR_BG, padx=25, pady=20)

        # Header
        lbl_h = ttk.Label(view, text="📊 Analyse Exploratoire & Profilage des Variables", style="Header.TLabel")
        lbl_h.pack(anchor="w", pady=(0, 15))

        # Main Split: Left Column Profile Inspector, Right Matplotlib Visualizer
        paned = tk.PanedWindow(view, orient=tk.HORIZONTAL, bg=self.COLOR_BG, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left Panel (Profile Card)
        left_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=15, width=420)
        paned.add(left_f, minsize=380)

        tk.Label(left_f, text="Sélectionner une variable :", font=("Segoe UI", 10, "bold"), bg=self.COLOR_CARD).pack(anchor="w")
        self.eda_col_var = tk.StringVar()
        self.cb_eda_col = ttk.Combobox(left_f, textvariable=self.eda_col_var, state="readonly", font=("Segoe UI", 10))
        self.cb_eda_col.pack(fill=tk.X, pady=(4, 12))
        self.cb_eda_col.bind("<<ComboboxSelected>>", lambda e: self._on_eda_column_selected())

        # Column Profile Details (Text Box / Info Card)
        self.txt_col_profile = tk.Text(left_f, bg="#f8fafc", font=("Consolas", 9), relief="flat", bd=1, wrap="word")
        self.txt_col_profile.pack(fill=tk.BOTH, expand=True)

        # Right Panel (Matplotlib Canvas)
        right_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=10, pady=10)
        paned.add(right_f, minsize=500)

        chart_ctrl = tk.Frame(right_f, bg=self.COLOR_CARD)
        chart_ctrl.pack(fill=tk.X, pady=(0, 10))

        tk.Label(chart_ctrl, text="Type de graphique :", font=("Segoe UI", 9, "bold"), bg=self.COLOR_CARD).pack(side=tk.LEFT, padx=(0, 6))
        self.chart_type_var = tk.StringVar(value="Histogramme / Distribution")
        self.cb_chart_type = ttk.Combobox(
            chart_ctrl, textvariable=self.chart_type_var, state="readonly",
            values=["Histogramme / Distribution", "Boîte à moustaches (Boxplot)", "Fréquences (Bar Chart)", "Matrice de Corrélation"],
            width=26
        )
        self.cb_chart_type.pack(side=tk.LEFT)
        self.cb_chart_type.bind("<<ComboboxSelected>>", lambda e: self._render_eda_plot())

        btn_refresh_plot = tk.Button(chart_ctrl, text="🔄 Actualiser", bg="#e2e8f0", relief="flat", padx=10, pady=2, command=self._render_eda_plot)
        btn_refresh_plot.pack(side=tk.RIGHT)

        # Embedded Figure
        self.fig = Figure(figsize=(5.5, 4.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_f)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return view

    def _refresh_eda_view(self):
        """Populates columns dropdown when navigating to EDA."""
        if not self.analysis_results or not self.cleaner:
            return
        cols = list(self.cleaner.df.columns)
        self.cb_eda_col["values"] = cols
        if cols and not self.eda_col_var.get():
            self.eda_col_var.set(cols[0])
            self._on_eda_column_selected()

    def _on_eda_column_selected(self):
        """Displays selected column profile and generates plot."""
        col = self.eda_col_var.get()
        profiles = self.analysis_results.get("profiles", {})
        if col not in profiles:
            return

        prof = profiles[col]
        stats = prof["stats"]

        lines = []
        lines.append(f"FICHE VARIABLE : {col}")
        lines.append("=" * 40)
        lines.append(f"Type détecté   : {prof['detected_type']}")
        lines.append(f"Niveau Confiance: {prof['confidence']} ({int(prof['confidence_score']*100)}%)")
        lines.append(f"Dtype Pandas   : {prof['pandas_dtype']}")
        lines.append("")
        lines.append(f"Observations   : {stats.get('total_count')} ({stats.get('non_null_count')} renseignées)")
        lines.append(f"Manquantes     : {stats.get('missing_count')} ({stats.get('missing_pct')}%)")
        lines.append(f"Distinctes     : {stats.get('unique_count')} ({stats.get('unique_pct')}%)")
        lines.append("")

        if "mean" in stats:
            lines.append("STATISTIQUES DESCRIPTIVES :")
            lines.append(f"  Moyenne      : {stats.get('mean')}")
            lines.append(f"  Médiane      : {stats.get('median')}")
            lines.append(f"  Écart-type   : {stats.get('std')}")
            lines.append(f"  Min / Max    : {stats.get('min')} / {stats.get('max')}")
            lines.append(f"  Q25 / Q75    : {stats.get('q25')} / {stats.get('q75')}")
            lines.append(f"  Outliers IQR : {stats.get('outliers_iqr_count', 0)} ({stats.get('outliers_iqr_pct', 0)}%)")
            lines.append("")

        if "top_values" in stats:
            lines.append("MODALITÉS LES PLUS FRÉQUENTES :")
            for k, v in stats["top_values"].items():
                lines.append(f"  • {k} : {v}")
            lines.append("")

        if prof["issues"]:
            lines.append("PROBLÈMES IDENTIFIÉS :")
            for iss in prof["issues"]:
                lines.append(f"  ⚠️ [{iss['severity']}] {iss['issue']} : {iss['details']}")
            lines.append("")

        if prof["recommendations"]:
            lines.append("RECOMMANDATIONS MÉTHODOLOGIQUES :")
            for rec in prof["recommendations"]:
                lines.append(f"  💡 {rec['action']}")
                lines.append(f"     -> {rec['justification']}")

        self.txt_col_profile.delete("1.0", tk.END)
        self.txt_col_profile.insert("1.0", "\n".join(lines))

        self._render_eda_plot()

    def _render_eda_plot(self):
        """Draws matplotlib visualization for the selected column."""
        if self.cleaner is None:
            return
        df = self.cleaner.df
        col = self.eda_col_var.get()
        chart_type = self.chart_type_var.get()

        self.ax.clear()

        try:
            if chart_type == "Matrice de Corrélation":
                corr = df.select_dtypes(include=[np.number]).corr()
                if not corr.empty and len(corr.columns) > 1:
                    cax = self.ax.matshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
                    self.fig.colorbar(cax, ax=self.ax, fraction=0.046, pad=0.04)
                    self.ax.set_xticks(range(len(corr.columns)))
                    self.ax.set_yticks(range(len(corr.columns)))
                    self.ax.set_xticklabels(corr.columns, rotation=45, ha="left", fontsize=8)
                    self.ax.set_yticklabels(corr.columns, fontsize=8)
                    self.ax.set_title("Matrice de Corrélation de Pearson", pad=20, fontsize=10, fontweight="bold")
                else:
                    self.ax.text(0.5, 0.5, "Pas assez de variables numériques pour la corrélation.", ha="center", va="center")

            elif col in df.columns:
                series = df[col].dropna()
                if chart_type == "Histogramme / Distribution":
                    if pd.api.types.is_numeric_dtype(series):
                        self.ax.hist(series, bins=25, color="#3b82f6", edgecolor="white", alpha=0.8)
                        self.ax.set_title(f"Distribution de {col}", fontsize=10, fontweight="bold")
                        self.ax.set_xlabel(col)
                        self.ax.set_ylabel("Effectif")
                    else:
                        self.ax.text(0.5, 0.5, "Variable non numérique pour histogramme.\nSélectionnez 'Fréquences'.", ha="center", va="center")

                elif chart_type == "Boîte à moustaches (Boxplot)":
                    if pd.api.types.is_numeric_dtype(series):
                        self.ax.boxplot(series, vert=True, patch_artist=True, boxprops=dict(facecolor="#93c5fd", color="#1d4ed8"))
                        self.ax.set_title(f"Boxplot de {col}", fontsize=10, fontweight="bold")
                        self.ax.set_ylabel(col)
                    else:
                        self.ax.text(0.5, 0.5, "Variable non numérique pour Boxplot.", ha="center", va="center")

                elif chart_type == "Fréquences (Bar Chart)":
                    top_vals = series.value_counts().head(12)
                    self.ax.barh([str(k) for k in top_vals.index], top_vals.values, color="#6366f1")
                    self.ax.set_title(f"Fréquences des modalités : {col}", fontsize=10, fontweight="bold")
                    self.ax.set_xlabel("Effectif")
                    self.ax.invert_yaxis()

            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Erreur de tracé : {e}", ha="center", va="center")
            self.canvas.draw()

    # -------------------------------------------------------------------------
    # 3. AUDIT DE QUALITÉ
    # -------------------------------------------------------------------------
    def _build_audit_view(self) -> tk.Frame:
        view = tk.Frame(self.content_frame, bg=self.COLOR_BG, padx=25, pady=20)

        # Header with Filter & Quick Clean button
        top_bar = tk.Frame(view, bg=self.COLOR_BG)
        top_bar.pack(fill=tk.X, pady=(0, 15))
        lbl_h = ttk.Label(top_bar, text="🔍 Audit Automatique de la Qualité des Données", style="Header.TLabel")
        lbl_h.pack(side=tk.LEFT)

        btn_auto_clean = tk.Button(
            top_bar, text="✨ Nettoyer Automatiquement les Recommandations Sûres",
            bg="#16a34a", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6,
            command=self._action_auto_clean_safe
        )
        btn_auto_clean.pack(side=tk.RIGHT)

        # Treeview for quality issues
        tree_f = tk.Frame(view, bg=self.COLOR_CARD, relief="solid", bd=1)
        tree_f.pack(fill=tk.BOTH, expand=True)

        cols = ("Variable", "Problème", "Impact", "Gravité", "Action Recommandée", "Justification", "État")
        self.tree_audit = ttk.Treeview(tree_f, columns=cols, show="headings", selectmode="browse")

        col_widths = {"Variable": 120, "Problème": 160, "Impact": 100, "Gravité": 90, "Action Recommandée": 160, "Justification": 260, "État": 80}
        for c in cols:
            self.tree_audit.heading(c, text=c)
            self.tree_audit.column(c, width=col_widths.get(c, 100), stretch=True)

        sc_y = ttk.Scrollbar(tree_f, orient="vertical", command=self.tree_audit.yview)
        self.tree_audit.configure(yscrollcommand=sc_y.set)
        sc_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_audit.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tag colors
        self.tree_audit.tag_configure("Critique", background="#fee2e2")
        self.tree_audit.tag_configure("Élevée", background="#ffedd5")
        self.tree_audit.tag_configure("Moyenne", background="#fef9c3")
        self.tree_audit.tag_configure("Faible", background="#f0fdf4")

        return view

    def _refresh_audit_view(self):
        """Refreshes the audit issues table."""
        self.tree_audit.delete(*self.tree_audit.get_children())
        issues = self.analysis_results.get("global_issues", [])
        for iss in issues:
            vals = (
                str(iss.get("variable", "")),
                str(iss.get("issue", "")),
                f"{iss.get('affected_count', 0)} ({iss.get('affected_pct', 0)}%)",
                str(iss.get("severity", "")),
                str(iss.get("action", "")),
                str(iss.get("justification", "")),
                str(iss.get("status", "À traiter"))
            )
            self.tree_audit.insert("", "end", values=vals, tags=(str(iss.get("severity", "")),))

    def _action_auto_clean_safe(self):
        """Applies safe cleaning: removes duplicates, strips text spaces, drops constants, imputes low missing."""
        if self.cleaner is None:
            return

        confirm = messagebox.askyesno(
            "Confirmer le nettoyage automatique sûr",
            "Cette opération va appliquer automatiquement :\n"
            "• La suppression des lignes dupliquées\n"
            "• Le nettoyage des espaces superflus (strip) dans le texte\n"
            "• La suppression des colonnes constantes (variance nulle)\n"
            "• L'imputation médiane/mode pour les faibles valeurs manquantes (<5%)\n\n"
            "Voulez-vous continuer ?"
        )
        if not confirm:
            return

        def worker():
            # 1. Duplicates
            self.cleaner.remove_duplicates()

            # 2. Columns
            profiles = self.analysis_results.get("profiles", {})
            for col, prof in profiles.items():
                if col not in self.cleaner.df.columns:
                    continue

                # Strip text
                if pd.api.types.is_object_dtype(self.cleaner.df[col]):
                    self.cleaner.clean_text_column(col, strip=True, casing=None, empty_to_nan=True)

                # Drop constant
                if prof["detected_type"] == VariableType.CONSTANT:
                    self.cleaner.drop_columns([col])
                    continue

                # Impute low missing
                stats = prof["stats"]
                if 0 < stats.get("missing_pct", 0) <= 5.0:
                    if prof["detected_type"] in [VariableType.NUMERIC_CONTINUOUS, VariableType.NUMERIC_DISCRETE]:
                        self.cleaner.impute_missing(col, strategy="median")
                    elif prof["detected_type"] in [VariableType.CATEGORICAL_NOMINAL, VariableType.BOOLEAN]:
                        self.cleaner.impute_missing(col, strategy="mode")

            # Re-analyze
            analyzer = DataAnalyzer()
            return analyzer.analyze_dataset(self.cleaner.df)

        def on_success(results):
            self.analysis_results = results
            self._update_preview_table(self.cleaner.df)
            messagebox.showinfo("Nettoyage Réussi", "Les opérations sûres ont été appliquées avec succès !")
            self.switch_section("cleaning")

        self.run_async(worker, on_success=on_success, busy_msg="Application des opérations de nettoyage sûres...")

    # -------------------------------------------------------------------------
    # 4. NETTOYAGE DES DONNÉES
    # -------------------------------------------------------------------------
    def _build_cleaning_view(self) -> tk.Frame:
        view = tk.Frame(self.content_frame, bg=self.COLOR_BG, padx=25, pady=20)

        # Header
        lbl_h = ttk.Label(view, text="🧹 Opérations de Nettoyage Interactif", style="Header.TLabel")
        lbl_h.pack(anchor="w", pady=(0, 15))

        paned = tk.PanedWindow(view, orient=tk.HORIZONTAL, bg=self.COLOR_BG, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left Panel : Tools
        left_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=15, width=440)
        paned.add(left_f, minsize=400)

        notebook = ttk.Notebook(left_f)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Imputation
        tab_imp = tk.Frame(notebook, bg=self.COLOR_CARD, padx=10, pady=10)
        notebook.add(tab_imp, text="Imputation")

        tk.Label(tab_imp, text="Variable à imputer :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.imp_col_var = tk.StringVar()
        self.cb_imp_col = ttk.Combobox(tab_imp, textvariable=self.imp_col_var, state="readonly")
        self.cb_imp_col.pack(fill=tk.X, pady=(0, 10))

        tk.Label(tab_imp, text="Stratégie d'imputation :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.imp_strat_var = tk.StringVar(value="median")
        cb_strat = ttk.Combobox(
            tab_imp, textvariable=self.imp_strat_var, state="readonly",
            values=["median", "mean", "mode", "constant", "drop_rows", "knn"]
        )
        cb_strat.pack(fill=tk.X, pady=(0, 10))

        tk.Label(tab_imp, text="Valeur de remplacement (si 'constant') :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.imp_val_var = tk.StringVar(value="Inconnu")
        tk.Entry(tab_imp, textvariable=self.imp_val_var).pack(fill=tk.X, pady=(0, 15))

        tk.Button(tab_imp, text="Appliquer l'imputation", bg=self.COLOR_PRIMARY, fg="white", relief="flat", pady=6, command=self._action_apply_imputation).pack(fill=tk.X)

        # Tab 2: Outliers
        tab_out = tk.Frame(notebook, bg=self.COLOR_CARD, padx=10, pady=10)
        notebook.add(tab_out, text="Outliers")

        tk.Label(tab_out, text="Variable numérique :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.out_col_var = tk.StringVar()
        self.cb_out_col = ttk.Combobox(tab_out, textvariable=self.out_col_var, state="readonly")
        self.cb_out_col.pack(fill=tk.X, pady=(0, 10))

        tk.Label(tab_out, text="Méthode de détection :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.out_method_var = tk.StringVar(value="iqr")
        ttk.Combobox(tab_out, textvariable=self.out_method_var, values=["iqr", "zscore"], state="readonly").pack(fill=tk.X, pady=(0, 10))

        tk.Label(tab_out, text="Action à appliquer :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.out_action_var = tk.StringVar(value="clip")
        ttk.Combobox(tab_out, textvariable=self.out_action_var, values=["clip", "nan", "drop"], state="readonly").pack(fill=tk.X, pady=(0, 15))

        tk.Button(tab_out, text="Traiter les valeurs aberrantes", bg=self.COLOR_PRIMARY, fg="white", relief="flat", pady=6, command=self._action_apply_outliers).pack(fill=tk.X)

        # Tab 3: Texte & Doublons
        tab_txt = tk.Frame(notebook, bg=self.COLOR_CARD, padx=10, pady=10)
        notebook.add(tab_txt, text="Texte & Doublons")

        tk.Label(tab_txt, text="Colonne de texte :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.txt_col_var = tk.StringVar()
        self.cb_txt_col = ttk.Combobox(tab_txt, textvariable=self.txt_col_var, state="readonly")
        self.cb_txt_col.pack(fill=tk.X, pady=(0, 10))

        self.chk_strip = tk.BooleanVar(value=True)
        tk.Checkbutton(tab_txt, text="Supprimer les espaces (strip)", variable=self.chk_strip, bg=self.COLOR_CARD).pack(anchor="w")

        tk.Label(tab_txt, text="Normalisation de la casse :", bg=self.COLOR_CARD).pack(anchor="w", pady=(6, 2))
        self.txt_case_var = tk.StringVar(value="lower")
        ttk.Combobox(tab_txt, textvariable=self.txt_case_var, values=["lower", "upper", "title", "none"], state="readonly").pack(fill=tk.X, pady=(0, 10))

        tk.Button(tab_txt, text="Nettoyer la colonne texte", bg=self.COLOR_PRIMARY, fg="white", relief="flat", pady=6, command=self._action_clean_text).pack(fill=tk.X, pady=(0, 15))

        tk.Frame(tab_txt, height=1, bg="#e2e8f0").pack(fill=tk.X, pady=8)
        tk.Button(tab_txt, text="🗑️ Supprimer les lignes dupliquées", bg="#e2e8f0", relief="flat", pady=6, command=self._action_remove_duplicates).pack(fill=tk.X)

        # Right Panel : Changelog & History
        right_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=15)
        paned.add(right_f, minsize=480)

        ctrl_hist = tk.Frame(right_f, bg=self.COLOR_CARD)
        ctrl_hist.pack(fill=tk.X, pady=(0, 10))
        tk.Label(ctrl_hist, text="Journal des opérations de nettoyage :", font=("Segoe UI", 10, "bold"), bg=self.COLOR_CARD).pack(side=tk.LEFT)

        btn_reset = tk.Button(ctrl_hist, text="🔄 Réinitialiser (Reset)", bg="#fee2e2", fg="#b91c1c", relief="flat", padx=8, pady=4, command=self._action_reset_cleaner)
        btn_reset.pack(side=tk.RIGHT, padx=4)

        btn_undo = tk.Button(ctrl_hist, text="↩️ Annuler (Undo)", bg="#e2e8f0", relief="flat", padx=8, pady=4, command=self._action_undo_cleaner)
        btn_undo.pack(side=tk.RIGHT)

        tree_hist_f = tk.Frame(right_f, bg=self.COLOR_CARD)
        tree_hist_f.pack(fill=tk.BOTH, expand=True)

        cols_h = ("Heure", "Opération", "Colonne", "Stratégie", "Détails")
        self.tree_history = ttk.Treeview(tree_hist_f, columns=cols_h, show="headings")
        for c in cols_h:
            self.tree_history.heading(c, text=c)
            self.tree_history.column(c, width=100, stretch=True)

        sc_h = ttk.Scrollbar(tree_hist_f, orient="vertical", command=self.tree_history.yview)
        self.tree_history.configure(yscrollcommand=sc_h.set)
        sc_h.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return view

    def _refresh_cleaning_view(self):
        """Refreshes dropdowns and history table."""
        if self.cleaner is None:
            return
        cols = list(self.cleaner.df.columns)
        num_cols = self.cleaner.df.select_dtypes(include=[np.number]).columns.tolist()
        str_cols = self.cleaner.df.select_dtypes(include=["object", "string"]).columns.tolist()

        self.cb_imp_col["values"] = cols
        self.cb_out_col["values"] = num_cols
        self.cb_txt_col["values"] = str_cols

        # Update History Table
        self.tree_history.delete(*self.tree_history.get_children())
        for h in self.cleaner.get_history():
            self.tree_history.insert("", "end", values=(
                h.get("timestamp", "").split()[-1],
                h.get("operation", ""),
                h.get("column", ""),
                h.get("strategy", ""),
                h.get("details", "")
            ))

    def _action_apply_imputation(self):
        col = self.imp_col_var.get()
        strat = self.imp_strat_var.get()
        val = self.imp_val_var.get()
        if not col or not self.cleaner:
            messagebox.showwarning("Attention", "Veuillez sélectionner une colonne.")
            return

        try:
            self.cleaner.impute_missing(col, strategy=strat, fill_value=val)
            self._update_preview_table(self.cleaner.df)
            self._refresh_cleaning_view()
            messagebox.showinfo("Succès", f"Imputation réussie pour '{col}' avec la stratégie '{strat}'.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _action_apply_outliers(self):
        col = self.out_col_var.get()
        method = self.out_method_var.get()
        action = self.out_action_var.get()
        if not col or not self.cleaner:
            messagebox.showwarning("Attention", "Veuillez sélectionner une variable numérique.")
            return

        try:
            _, cnt = self.cleaner.handle_outliers(col, method=method, action=action)
            self._update_preview_table(self.cleaner.df)
            self._refresh_cleaning_view()
            messagebox.showinfo("Succès", f"{cnt} outliers traités sur '{col}' via {method.upper()} ({action}).")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _action_clean_text(self):
        col = self.txt_col_var.get()
        casing = None if self.txt_case_var.get() == "none" else self.txt_case_var.get()
        if not col or not self.cleaner:
            messagebox.showwarning("Attention", "Veuillez sélectionner une variable texte.")
            return

        try:
            self.cleaner.clean_text_column(col, strip=self.chk_strip.get(), casing=casing)
            self._update_preview_table(self.cleaner.df)
            self._refresh_cleaning_view()
            messagebox.showinfo("Succès", f"Colonne texte '{col}' nettoyée.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _action_remove_duplicates(self):
        if not self.cleaner:
            return
        _, cnt = self.cleaner.remove_duplicates()
        self._update_preview_table(self.cleaner.df)
        self._refresh_cleaning_view()
        messagebox.showinfo("Doublons", f"{cnt} lignes dupliquées supprimées.")

    def _action_undo_cleaner(self):
        if not self.cleaner:
            return
        res = self.cleaner.undo()
        if res is not None:
            self._update_preview_table(self.cleaner.df)
            self._refresh_cleaning_view()
            messagebox.showinfo("Annulation", "La dernière action de nettoyage a été annulée.")
        else:
            messagebox.showinfo("Info", "Aucune action antérieure à annuler.")

    def _action_reset_cleaner(self):
        if not self.cleaner:
            return
        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir réinitialiser le dataset à son état d'origine ?"):
            self.cleaner.reset()
            self._update_preview_table(self.cleaner.df)
            self._refresh_cleaning_view()
            messagebox.showinfo("Réinitialisation", "Dataset réinitialisé à son état d'importation.")

    # -------------------------------------------------------------------------
    # 5. TRANSFORMATIONS & FEATURE ENGINEERING
    # -------------------------------------------------------------------------
    def _build_transforms_view(self) -> tk.Frame:
        view = tk.Frame(self.content_frame, bg=self.COLOR_BG, padx=25, pady=20)

        lbl_h = ttk.Label(view, text="⚙️ Transformation des Variables & Feature Engineering", style="Header.TLabel")
        lbl_h.pack(anchor="w", pady=(0, 15))

        paned = tk.PanedWindow(view, orient=tk.HORIZONTAL, bg=self.COLOR_BG, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left tools
        left_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=15, width=440)
        paned.add(left_f, minsize=400)

        nb = ttk.Notebook(left_f)
        nb.pack(fill=tk.BOTH, expand=True)

        # Temporal tab
        tab_dt = tk.Frame(nb, bg=self.COLOR_CARD, padx=10, pady=10)
        nb.add(tab_dt, text="Temporel")
        tk.Label(tab_dt, text="Colonne de Date/Heure :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.dt_col_var = tk.StringVar()
        self.cb_dt_col = ttk.Combobox(tab_dt, textvariable=self.dt_col_var, state="readonly")
        self.cb_dt_col.pack(fill=tk.X, pady=(0, 10))

        self.chk_dt_year = tk.BooleanVar(value=True)
        self.chk_dt_month = tk.BooleanVar(value=True)
        self.chk_dt_day = tk.BooleanVar(value=True)
        self.chk_dt_wknd = tk.BooleanVar(value=True)
        tk.Checkbutton(tab_dt, text="Extraire Année (Year)", variable=self.chk_dt_year, bg=self.COLOR_CARD).pack(anchor="w")
        tk.Checkbutton(tab_dt, text="Extraire Mois (Month)", variable=self.chk_dt_month, bg=self.COLOR_CARD).pack(anchor="w")
        tk.Checkbutton(tab_dt, text="Extraire Jour (Day)", variable=self.chk_dt_day, bg=self.COLOR_CARD).pack(anchor="w")
        tk.Checkbutton(tab_dt, text="Indicateur Week-end (Is Weekend)", variable=self.chk_dt_wknd, bg=self.COLOR_CARD).pack(anchor="w")

        tk.Button(tab_dt, text="Générer variables temporelles", bg=self.COLOR_PRIMARY, fg="white", relief="flat", pady=6, command=self._action_extract_temporal).pack(fill=tk.X, pady=15)

        # Interaction tab
        tab_inter = tk.Frame(nb, bg=self.COLOR_CARD, padx=10, pady=10)
        nb.add(tab_inter, text="Combinaison")
        tk.Label(tab_inter, text="Colonne A (Numérique) :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.inter_col_a = tk.StringVar()
        self.cb_inter_a = ttk.Combobox(tab_inter, textvariable=self.inter_col_a, state="readonly")
        self.cb_inter_a.pack(fill=tk.X, pady=(0, 6))

        tk.Label(tab_inter, text="Opération :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.inter_op = tk.StringVar(value="ratio")
        ttk.Combobox(tab_inter, textvariable=self.inter_op, values=["ratio", "multiply", "sum", "diff"], state="readonly").pack(fill=tk.X, pady=(0, 6))

        tk.Label(tab_inter, text="Colonne B (Numérique) :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.inter_col_b = tk.StringVar()
        self.cb_inter_b = ttk.Combobox(tab_inter, textvariable=self.inter_col_b, state="readonly")
        self.cb_inter_b.pack(fill=tk.X, pady=(0, 10))

        tk.Button(tab_inter, text="Créer interaction numérique", bg=self.COLOR_PRIMARY, fg="white", relief="flat", pady=6, command=self._action_create_interaction).pack(fill=tk.X, pady=10)

        # Discretization tab
        tab_bin = tk.Frame(nb, bg=self.COLOR_CARD, padx=10, pady=10)
        nb.add(tab_bin, text="Discrétisation")
        tk.Label(tab_bin, text="Variable à discrétiser :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.bin_col_var = tk.StringVar()
        self.cb_bin_col = ttk.Combobox(tab_bin, textvariable=self.bin_col_var, state="readonly")
        self.cb_bin_col.pack(fill=tk.X, pady=(0, 6))

        tk.Label(tab_bin, text="Nombre d'intervalles (bins) :", bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 2))
        self.bin_n_var = tk.IntVar(value=5)
        tk.Spinbox(tab_bin, from_=2, to=20, textvariable=self.bin_n_var).pack(fill=tk.X, pady=(0, 6))

        tk.Button(tab_bin, text="Appliquer Discrétisation", bg=self.COLOR_PRIMARY, fg="white", relief="flat", pady=6, command=self._action_apply_binning).pack(fill=tk.X, pady=10)

        # Right Panel: Created features table
        right_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=15)
        paned.add(right_f, minsize=480)

        tk.Label(right_f, text="Nouvelles caractéristiques créées :", font=("Segoe UI", 10, "bold"), bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 10))

        tree_f = tk.Frame(right_f, bg=self.COLOR_CARD)
        tree_f.pack(fill=tk.BOTH, expand=True)

        cols_f = ("Type", "Source", "Colonnes Générées", "Justification")
        self.tree_feat = ttk.Treeview(tree_f, columns=cols_f, show="headings")
        for c in cols_f:
            self.tree_feat.heading(c, text=c)
            self.tree_feat.column(c, width=120, stretch=True)

        sc_f = ttk.Scrollbar(tree_f, orient="vertical", command=self.tree_feat.yview)
        self.tree_feat.configure(yscrollcommand=sc_f.set)
        sc_f.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_feat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return view

    def _refresh_transforms_view(self):
        if not self.cleaner:
            return
        cols = list(self.cleaner.df.columns)
        num_cols = self.cleaner.df.select_dtypes(include=[np.number]).columns.tolist()

        self.cb_dt_col["values"] = cols
        self.cb_inter_a["values"] = num_cols
        self.cb_inter_b["values"] = num_cols
        self.cb_bin_col["values"] = num_cols

        # Update table
        self.tree_feat.delete(*self.tree_feat.get_children())
        if self.transformer:
            for feat in self.transformer.get_created_features_log():
                self.tree_feat.insert("", "end", values=(
                    feat.get("type"),
                    feat.get("source_column"),
                    ", ".join(feat.get("created_columns", [])),
                    feat.get("justification")
                ))

    def _action_extract_temporal(self):
        col = self.dt_col_var.get()
        if not col or not self.cleaner:
            return
        self.transformer = FeatureTransformer(self.cleaner.df)
        df_new, new_cols = self.transformer.extract_datetime_features(
            col,
            extract_year=self.chk_dt_year.get(),
            extract_month=self.chk_dt_month.get(),
            extract_day=self.chk_dt_day.get(),
            extract_is_weekend=self.chk_dt_wknd.get()
        )
        self.cleaner.df = df_new
        self._update_preview_table(self.cleaner.df)
        self._refresh_transforms_view()
        messagebox.showinfo("Succès", f"Variables créées : {', '.join(new_cols)}")

    def _action_create_interaction(self):
        a = self.inter_col_a.get()
        b = self.inter_col_b.get()
        op = self.inter_op.get()
        if not a or not b or not self.cleaner:
            return
        if self.transformer is None:
            self.transformer = FeatureTransformer(self.cleaner.df)
        else:
            self.transformer.df = self.cleaner.df

        df_new, new_col = self.transformer.create_numeric_interaction(a, b, operation=op)
        self.cleaner.df = df_new
        self._update_preview_table(self.cleaner.df)
        self._refresh_transforms_view()
        messagebox.showinfo("Succès", f"Nouvelle variable d'interaction créée : {new_col}")

    def _action_apply_binning(self):
        col = self.bin_col_var.get()
        n = self.bin_n_var.get()
        if not col or not self.cleaner:
            return
        if self.transformer is None:
            self.transformer = FeatureTransformer(self.cleaner.df)
        else:
            self.transformer.df = self.cleaner.df

        df_new, new_col = self.transformer.bin_numeric_column(col, n_bins=n)
        self.cleaner.df = df_new
        self._update_preview_table(self.cleaner.df)
        self._refresh_transforms_view()
        messagebox.showinfo("Succès", f"Variable discrétisée créée : {new_col}")

    # -------------------------------------------------------------------------
    # 6. CONFIGURATION MACHINE LEARNING
    # -------------------------------------------------------------------------
    def _build_ml_view(self) -> tk.Frame:
        view = tk.Frame(self.content_frame, bg=self.COLOR_BG, padx=25, pady=20)

        lbl_h = ttk.Label(view, text="🤖 Configuration de la Préparation Machine Learning", style="Header.TLabel")
        lbl_h.pack(anchor="w", pady=(0, 15))

        paned = tk.PanedWindow(view, orient=tk.HORIZONTAL, bg=self.COLOR_BG, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left: Settings
        left_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=15, width=440)
        paned.add(left_f, minsize=400)

        tk.Label(left_f, text="Type d'apprentissage :", font=("Segoe UI", 10, "bold"), bg=self.COLOR_CARD).pack(anchor="w")
        self.ml_mode_var = tk.StringVar(value="supervised")
        f_mode = tk.Frame(left_f, bg=self.COLOR_CARD)
        f_mode.pack(fill=tk.X, pady=(4, 12))
        tk.Radiobutton(f_mode, text="Apprentissage Supervisé", variable=self.ml_mode_var, value="supervised", bg=self.COLOR_CARD, command=self._on_ml_mode_changed).pack(side=tk.LEFT)
        tk.Radiobutton(f_mode, text="Non Supervisé", variable=self.ml_mode_var, value="unsupervised", bg=self.COLOR_CARD, command=self._on_ml_mode_changed).pack(side=tk.LEFT, padx=15)

        # Target selector frame
        self.target_frame = tk.Frame(left_f, bg=self.COLOR_CARD)
        self.target_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(self.target_frame, text="Variable Cible (Target y) :", font=("Segoe UI", 9, "bold"), bg=self.COLOR_CARD).pack(anchor="w")
        self.target_var = tk.StringVar()
        self.cb_target = ttk.Combobox(self.target_frame, textvariable=self.target_var, state="readonly")
        self.cb_target.pack(fill=tk.X, pady=(4, 6))
        self.cb_target.bind("<<ComboboxSelected>>", lambda e: self._on_target_selected())

        self.lbl_task_detected = tk.Label(self.target_frame, text="Tâche : Non définie", font=("Segoe UI", 9, "italic"), bg=self.COLOR_CARD, fg="#2563eb")
        self.lbl_task_detected.pack(anchor="w")

        # Split settings
        self.split_frame = tk.Frame(left_f, bg=self.COLOR_CARD)
        self.split_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(self.split_frame, text="Stratégie de partitionnement (Split) :", font=("Segoe UI", 9, "bold"), bg=self.COLOR_CARD).pack(anchor="w")
        self.split_strat_var = tk.StringVar(value="stratified")
        ttk.Combobox(self.split_frame, textvariable=self.split_strat_var, values=["stratified", "random"], state="readonly").pack(fill=tk.X, pady=(4, 6))

        tk.Label(self.split_frame, text="Proportion de l'ensemble de Test :", bg=self.COLOR_CARD).pack(anchor="w")
        self.test_size_var = tk.DoubleVar(value=0.20)
        self.scale_test = tk.Scale(self.split_frame, variable=self.test_size_var, from_=0.10, to=0.40, resolution=0.05, orient=tk.HORIZONTAL, bg=self.COLOR_CARD)
        self.scale_test.pack(fill=tk.X, pady=(0, 10))

        # Pipeline transformation params
        tk.Label(left_f, text="Mise à l'échelle numérique :", font=("Segoe UI", 9, "bold"), bg=self.COLOR_CARD).pack(anchor="w")
        self.scaler_var = tk.StringVar(value="standard")
        ttk.Combobox(left_f, textvariable=self.scaler_var, values=["standard", "minmax", "robust", "none"], state="readonly").pack(fill=tk.X, pady=(4, 10))

        tk.Label(left_f, text="Encodage catégoriel :", font=("Segoe UI", 9, "bold"), bg=self.COLOR_CARD).pack(anchor="w")
        self.encoder_var = tk.StringVar(value="onehot")
        ttk.Combobox(left_f, textvariable=self.encoder_var, values=["onehot", "ordinal"], state="readonly").pack(fill=tk.X, pady=(4, 15))

        btn_prepare = tk.Button(
            left_f, text="⚙️ Générer Pipeline & Préparer les Données",
            bg=self.COLOR_PRIMARY, fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", pady=8, command=self._action_generate_ml_pipeline
        )
        btn_prepare.pack(fill=tk.X)

        # Right: Algorithm Recommendations & Leakage audit
        right_f = tk.Frame(paned, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=15)
        paned.add(right_f, minsize=480)

        tk.Label(right_f, text="Modèles ML Recommandés & Guide Méthodologique :", font=("Segoe UI", 10, "bold"), bg=self.COLOR_CARD).pack(anchor="w", pady=(0, 10))

        self.txt_ml_guide = tk.Text(right_f, bg="#f8fafc", font=("Segoe UI", 9), relief="flat", bd=1, wrap="word")
        self.txt_ml_guide.pack(fill=tk.BOTH, expand=True)

        return view

    def _refresh_ml_view(self):
        if not self.cleaner:
            return
        cols = list(self.cleaner.df.columns)
        self.cb_target["values"] = cols

    def _on_ml_mode_changed(self):
        if self.ml_mode_var.get() == "supervised":
            self.target_frame.pack(fill=tk.X, pady=(0, 10))
            self.split_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.target_frame.pack_forget()
            self.split_frame.pack_forget()

    def _on_target_selected(self):
        col = self.target_var.get()
        if not col or not self.cleaner:
            return
        task, info = MLPreprocessor.infer_task_type(self.cleaner.df[col])
        self.lbl_task_detected.config(text=f"Tâche : {task}")

        # Update guide
        recs = {
            MLTaskType.BINARY_CLASSIFICATION: [
                "• Régression Logistique : Robuste, nécessite StandardScaler ou RobustScaler.",
                "• Random Forest : Très puissant, capture non-linéarités, insensible au scaling.",
                "• SVM : Idéal pour séparations complexes, mise à l'échelle impérative.",
                "• KNN : Basé sur les distances, standardisation obligatoire."
            ],
            MLTaskType.REGRESSION: [
                "• Régression Linéaire / Ridge : Rapide, scaling indispensable pour régularisation.",
                "• Random Forest Regressor : Capture les interactions complexes sans mise à l'échelle.",
                "• Gradient Boosting : Hautes performances prédictives."
            ],
            MLTaskType.MULTICLASS_CLASSIFICATION: [
                "• Random Forest Classifier : Excellent choix par défaut pour plusieurs classes.",
                "• Régression Logistique Multinomiale : Référence linéaire rapide."
            ]
        }.get(task, [])

        txt = []
        txt.append(f"TÂCHE IDENTIFIÉE : {task}")
        txt.append("=" * 40)
        if info.get("is_imbalanced"):
            txt.append(f"⚠️ AVERTISSEMENT : {info.get('warning')}")
            txt.append(f"Distribution : {info.get('class_percentages')}")
            txt.append("Recommandation : Utiliser la stratégie de split 'stratified' (présélectionnée).\n")
        else:
            txt.append("✅ Équilibre des classes satisfaisant.\n")

        txt.append("ALGORITHMES ADAPTÉS :")
        txt.extend(recs)
        txt.append("\nPRÉVENTION DES FUITES DE DONNÉES (ZERO-LEAKAGE) :")
        txt.append("• Les estimateurs (moyenne, médiane, échelles, fréquences) sont appris STRICTEMENT sur X_train.")
        txt.append("• X_test est transformé à l'aide des paramètres de X_train sans aucun recalcul.")

        self.txt_ml_guide.delete("1.0", tk.END)
        self.txt_ml_guide.insert("1.0", "\n".join(txt))

    def _action_generate_ml_pipeline(self):
        if not self.cleaner:
            return

        mode = self.ml_mode_var.get()
        target = self.target_var.get()

        if mode == "supervised" and not target:
            messagebox.showwarning("Attention", "Veuillez sélectionner la variable cible y.")
            return

        def worker():
            preprocessor = MLPreprocessor(self.cleaner.df)
            if mode == "supervised":
                return preprocessor.build_supervised_pipeline(
                    target_col=target,
                    test_size=self.test_size_var.get(),
                    split_strategy=self.split_strat_var.get(),
                    numeric_scaler=self.scaler_var.get(),
                    categorical_encoder=self.encoder_var.get()
                )
            else:
                return preprocessor.build_unsupervised_pipeline(
                    numeric_scaler=self.scaler_var.get(),
                    categorical_encoder=self.encoder_var.get()
                )

        def on_success(results):
            self.ml_prep_results = results
            messagebox.showinfo("Pipeline Prête", "La préparation Machine Learning a été exécutée avec succès sans aucune fuite de données !\nConsultez la section 7 pour inspecter et exporter les résultats.")
            self.switch_section("export")

        self.run_async(worker, on_success=on_success, busy_msg="Construction et ajustement de la pipeline Scikit-learn...")

    # -------------------------------------------------------------------------
    # 7. RÉSULTATS & EXPORTATION
    # -------------------------------------------------------------------------
    def _build_export_view(self) -> tk.Frame:
        view = tk.Frame(self.content_frame, bg=self.COLOR_BG, padx=25, pady=20)

        lbl_h = ttk.Label(view, text="💾 Résultats de la Préparation & Centre d'Exportation", style="Header.TLabel")
        lbl_h.pack(anchor="w", pady=(0, 15))

        # Top summary card
        self.exp_summary_card = tk.Frame(view, bg=self.COLOR_CARD, relief="solid", bd=1, padx=15, pady=12)
        self.exp_summary_card.pack(fill=tk.X, pady=(0, 15))
        self.lbl_exp_summary = tk.Label(
            self.exp_summary_card,
            text="Aucune préparation ML effectuée pour le moment. Vous pouvez toujours exporter les données nettoyées.",
            font=("Segoe UI", 10), bg=self.COLOR_CARD, fg="#475569"
        )
        self.lbl_exp_summary.pack(anchor="w")

        # Table Preview of prepared data
        tbl_container = tk.Frame(view, bg=self.COLOR_CARD, relief="solid", bd=1)
        tbl_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        tbl_ctrl = tk.Frame(tbl_container, bg="#f1f5f9", padx=10, pady=6)
        tbl_ctrl.pack(fill=tk.X)
        tk.Label(tbl_ctrl, text="Aperçu des données préparées :", font=("Segoe UI", 9, "bold"), bg="#f1f5f9").pack(side=tk.LEFT)

        self.exp_split_choice = tk.StringVar(value="X_train")
        self.cb_exp_split = ttk.Combobox(tbl_ctrl, textvariable=self.exp_split_choice, state="readonly", values=["X_train", "X_test", "y_train", "y_test", "Nettoyées"], width=12)
        self.cb_exp_split.pack(side=tk.LEFT, padx=10)
        self.cb_exp_split.bind("<<ComboboxSelected>>", lambda e: self._on_exp_split_changed())

        # Treeview
        tree_scroll_f = tk.Frame(tbl_container, bg=self.COLOR_CARD)
        tree_scroll_f.pack(fill=tk.BOTH, expand=True)

        self.tree_export = ttk.Treeview(tree_scroll_f, show="headings", selectmode="browse")
        sc_ey = ttk.Scrollbar(tree_scroll_f, orient="vertical", command=self.tree_export.yview)
        sc_ex = ttk.Scrollbar(tree_scroll_f, orient="horizontal", command=self.tree_export.xview)
        self.tree_export.configure(yscrollcommand=sc_ey.set, xscrollcommand=sc_ex.set)

        sc_ey.pack(side=tk.RIGHT, fill=tk.Y)
        sc_ex.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_export.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Export Buttons Bar
        btn_grid = tk.Frame(view, bg=self.COLOR_BG)
        btn_grid.pack(fill=tk.X)

        tk.Button(btn_grid, text="📥 Exporter Données Nettoyées (CSV)", bg="#3b82f6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=8, command=lambda: self._action_export_cleaned("csv")).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(btn_grid, text="📥 Exporter Données Nettoyées (Excel)", bg="#2563eb", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=8, command=lambda: self._action_export_cleaned("excel")).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_grid, text="📦 Exporter Données ML (Splits)", bg="#4f46e5", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=8, command=self._action_export_ml_splits).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_grid, text="💾 Sauvegarder Pipeline (.joblib)", bg="#059669", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=8, command=self._action_export_joblib).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_grid, text="📄 Générer & Ouvrir le Rapport (HTML)", bg="#16a34a", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=8, command=self._action_generate_and_open_report).pack(side=tk.RIGHT)

        return view

    def _refresh_export_view(self):
        if self.ml_prep_results:
            mode = self.ml_prep_results.get("mode")
            if mode == "supervised":
                X_tr = self.ml_prep_results["X_train"]
                X_te = self.ml_prep_results["X_test"]
                self.lbl_exp_summary.config(
                    text=f"✅ Pipeline Supervisée ({self.ml_prep_results.get('task_type')}) prête !\n"
                         f"Train: {X_tr.shape[0]} lignes × {X_tr.shape[1]} variables | Test: {X_te.shape[0]} lignes × {X_te.shape[1]} variables."
                )
                self.cb_exp_split["values"] = ["X_train", "X_test", "y_train", "y_test", "Nettoyées"]
                self.exp_split_choice.set("X_train")
                self._update_export_tree(X_tr)
            else:
                X_pr = self.ml_prep_results["X_prepared"]
                self.lbl_exp_summary.config(text=f"✅ Données Non Supervisées préparées ({X_pr.shape[0]} lignes × {X_pr.shape[1]} variables).")
                self.cb_exp_split["values"] = ["X_prepared", "Nettoyées"]
                self.exp_split_choice.set("X_prepared")
                self._update_export_tree(X_pr)
        elif self.cleaner:
            self.lbl_exp_summary.config(text=f"Dataset nettoyé prêt à l'exportation ({len(self.cleaner.df)} lignes × {len(self.cleaner.df.columns)} colonnes).")
            self.cb_exp_split["values"] = ["Nettoyées"]
            self.exp_split_choice.set("Nettoyées")
            self._update_export_tree(self.cleaner.df)

    def _on_exp_split_changed(self):
        choice = self.exp_split_choice.get()
        if not self.ml_prep_results and choice == "Nettoyées" and self.cleaner:
            self._update_export_tree(self.cleaner.df)
            return

        if self.ml_prep_results:
            if choice == "X_train":
                self._update_export_tree(self.ml_prep_results["X_train"])
            elif choice == "X_test":
                self._update_export_tree(self.ml_prep_results["X_test"])
            elif choice == "y_train":
                self._update_export_tree(pd.DataFrame(self.ml_prep_results["y_train"]))
            elif choice == "y_test":
                self._update_export_tree(pd.DataFrame(self.ml_prep_results["y_test"]))
            elif choice == "X_prepared":
                self._update_export_tree(self.ml_prep_results["X_prepared"])
            elif choice == "Nettoyées" and self.cleaner:
                self._update_export_tree(self.cleaner.df)

    def _update_export_tree(self, df: pd.DataFrame):
        self.tree_export.delete(*self.tree_export.get_children())
        if df.empty:
            return

        cols = list(df.columns)
        self.tree_export["columns"] = cols
        for c in cols:
            self.tree_export.heading(c, text=c)
            self.tree_export.column(c, width=110, stretch=True)

        for _, row in df.head(50).iterrows():
            vals = [round(v, 4) if isinstance(v, float) else str(v) for v in row.values]
            self.tree_export.insert("", "end", values=vals)

    def _action_export_cleaned(self, fmt: str):
        if not self.cleaner:
            return
        try:
            path = self.export_manager.export_cleaned_dataset(self.cleaner.df, format_type=fmt)
            messagebox.showinfo("Exportation Réussie", f"Dataset nettoyé exporté avec succès dans :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _action_export_ml_splits(self):
        if not self.ml_prep_results:
            messagebox.showwarning("Attention", "Aucune pipeline ML n'a encore été générée (Section 6).")
            return
        try:
            paths = self.export_manager.export_ml_splits(self.ml_prep_results, format_type="csv")
            msg = "\n".join([f"• {k} : {p}" for k, p in paths.items()])
            messagebox.showinfo("Exportation Réussie", f"Fichiers ML exportés avec succès :\n{msg}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _action_export_joblib(self):
        if not self.ml_prep_results:
            messagebox.showwarning("Attention", "Aucune pipeline ML n'a encore été générée (Section 6).")
            return
        try:
            p_job = self.export_manager.export_pipeline_joblib(self.ml_prep_results)
            p_inf = self.export_manager.generate_inference_script()
            messagebox.showinfo("Exportation Réussie", f"Pipeline Scikit-learn sauvegardée :\n{p_job}\n\nScript d'inférence autonome généré :\n{p_inf}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _action_generate_and_open_report(self):
        if not self.analysis_results or not self.cleaner:
            messagebox.showwarning("Attention", "Veuillez charger un dataset et lancer l'analyse préalable.")
            return

        try:
            html_p = self.report_generator.generate_html_report(
                metadata=self.metadata,
                analysis_results=self.analysis_results,
                cleaning_history=self.cleaner.get_history(),
                created_features=self.transformer.get_created_features_log() if self.transformer else [],
                ml_prep_results=self.ml_prep_results
            )
            # Also generate markdown
            self.report_generator.generate_markdown_report(
                metadata=self.metadata,
                analysis_results=self.analysis_results,
                cleaning_history=self.cleaner.get_history(),
                created_features=self.transformer.get_created_features_log() if self.transformer else [],
                ml_prep_results=self.ml_prep_results
            )

            webbrowser.open(f"file://{os.path.abspath(html_p)}")
            messagebox.showinfo("Rapport Généré", f"Rapport de préparation complet généré et ouvert dans le navigateur web :\n{html_p}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
