"""
Module: core/report_generator.py
Description: Generates comprehensive, executive data preparation reports in HTML, Markdown, and Word,
             distinguishing executed actions from proposed recommendations with detailed explanations.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import html


def _normalize_dict_item(item):
    """Ensure report items are converted to standard dictionaries."""
    if hasattr(item, "to_dict"):
        return item.to_dict()
    if isinstance(item, dict):
        return item
    return {
        "timestamp": str(getattr(item, "timestamp", "")),
        "operation": str(getattr(item, "op_type", getattr(item, "operation", "Opération"))),
        "column": str(getattr(item, "column", "[Global]")),
        "strategy": str(getattr(item, "strategy", "")),
        "details": str(getattr(item, "details", "")),
        "params": getattr(item, "params", {}) or {}
    }


class ReportGenerator:
    """Generates detailed Data Preparation Audit & Workflow Reports."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        metadata: Dict[str, Any],
        analysis_results: Dict[str, Any],
        cleaning_history: List[Dict[str, Any]],
        created_features: List[Dict[str, Any]],
        ml_prep_results: Optional[Dict[str, Any]] = None,
        filename: str = "rapport_preparation.html"
    ) -> str:
        """
        Generates a standalone, beautifully styled HTML report.
        """
        cleaning_history = [_normalize_dict_item(x) for x in (cleaning_history or [])]
        created_features = [_normalize_dict_item(x) for x in (created_features or [])]
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        summary = analysis_results.get("summary", {})
        profiles = analysis_results.get("profiles", {})
        global_issues = analysis_results.get("global_issues", [])

        # Build Profiles Rows with detailed explanations
        profiles_rows_html = []
        for col, prof in profiles.items():
            conf_badge = f'<span class="badge badge-conf-{prof["confidence"].lower()}">{prof["confidence"]}</span>'
            stats = prof["stats"]
            issues_summary = ", ".join([i["issue"] for i in prof["issues"]]) if prof["issues"] else "Aucun problème"
            recs_summary = ", ".join([r["action"] for r in prof["recommendations"]]) if prof["recommendations"] else "Conserver tel quel"
            
            # Detailed explanation for type detection
            type_explanation = prof.get("meta", {}).get("reason", "Analyse statistique des valeurs")
            
            # Detailed explanation for recommendations
            recs_explanation = ""
            if prof["recommendations"]:
                recs_explanation = "<ul style='margin: 5px 0; padding-left: 20px;'>"
                for rec in prof["recommendations"]:
                    recs_explanation += f"<li><strong>{html.escape(rec['action'])}</strong> : {html.escape(rec.get('justification', 'Amélioration de la qualité des données'))}</li>"
                recs_explanation += "</ul>"

            row = f"""
            <tr>
                <td><strong>{html.escape(col)}</strong></td>
                <td>{html.escape(prof["detected_type"])}<br><small style="color: #64748b; font-size: 11px;">{html.escape(type_explanation)}</small></td>
                <td>{conf_badge}</td>
                <td>{stats.get("missing_count", 0)} ({stats.get("missing_pct", 0)}%)</td>
                <td>{stats.get("unique_count", 0)} ({stats.get("unique_pct", 0)}%)</td>
                <td><small>{html.escape(issues_summary)}</small></td>
                <td><small>{html.escape(recs_summary)}{recs_explanation}</small></td>
            </tr>
            """
            profiles_rows_html.append(row)

        # Build Global Issues Rows
        issues_rows_html = []
        for issue in global_issues:
            sev = issue.get("severity", "Moyenne")
            sev_class = {
                "Critique": "badge-danger",
                "Élevée": "badge-warning",
                "Moyenne": "badge-info",
                "Faible": "badge-success"
            }.get(sev, "badge-info")

            status = issue.get("status", "À traiter")
            status_class = "badge-success" if status == "Corrigé" else "badge-warning"

            row = f"""
            <tr>
                <td><strong>{html.escape(str(issue.get("variable", "")))}</strong></td>
                <td>{html.escape(str(issue.get("issue", "")))}</td>
                <td><span class="badge {sev_class}">{html.escape(sev)}</span></td>
                <td>{issue.get("affected_count", 0)} ({issue.get("affected_pct", 0)}%)</td>
                <td>{html.escape(str(issue.get("action", "")))}</td>
                <td><small>{html.escape(str(issue.get("justification", "")))}</small></td>
                <td><span class="badge {status_class}">{html.escape(status)}</span></td>
            </tr>
            """
            issues_rows_html.append(row)

        # Build Cleaning History Rows with detailed explanations
        history_rows_html = []
        if cleaning_history:
            for item in cleaning_history:
                operation = item.get("operation", "")
                strategy = item.get("strategy", "")
                details = item.get("details", "")
                
                # Detailed explanation for each cleaning operation
                explanation = ""
                if "imputation" in operation.lower():
                    explanation = f"Remplacement des valeurs manquantes par {strategy} pour préserver la distribution des données et éviter les biais."
                elif "outlier" in operation.lower():
                    explanation = f"Traitement des valeurs aberrantes ({strategy}) pour réduire l'impact des points extrêmes sur les modèles."
                elif "duplicate" in operation.lower():
                    explanation = "Suppression des lignes dupliquées pour éviter le sur-apprentissage sur des observations identiques."
                elif "text" in operation.lower():
                    explanation = "Normalisation du texte (espaces, casse) pour une meilleure cohérence des données catégorielles."
                
                row = f"""
                <tr>
                    <td><small>{html.escape(item.get("timestamp", ""))}</small></td>
                    <td><strong>{html.escape(operation)}</strong></td>
                    <td><code>{html.escape(item.get("column", ""))}</code></td>
                    <td>{html.escape(strategy)}</td>
                    <td>{html.escape(details)}<br><small style="color: #64748b;">{html.escape(explanation)}</small></td>
                </tr>
                """
                history_rows_html.append(row)
        else:
            history_rows_html.append("<tr><td colspan='5'><em>Aucune opération de nettoyage manuelle n'a été exécutée.</em></td></tr>")

        # Build Created Features Rows
        feat_rows_html = []
        if created_features:
            for feat in created_features:
                cols = ", ".join(feat.get("created_columns", []))
                row = f"""
                <tr>
                    <td><span class="badge badge-info">{html.escape(feat.get("type", ""))}</span></td>
                    <td><code>{html.escape(feat.get("source_column", ""))}</code></td>
                    <td><strong>{html.escape(cols)}</strong></td>
                    <td><small>{html.escape(feat.get("justification", ""))}</small></td>
                </tr>
                """
                feat_rows_html.append(row)
        else:
            feat_rows_html.append("<tr><td colspan='4'><em>Aucune nouvelle caractéristique créée.</em></td></tr>")

        # Build ML Configuration Section
        ml_section_html = "<p><em>Aucune pipeline Machine Learning n'a encore été configurée.</em></p>"
        if ml_prep_results:
            mode = ml_prep_results.get("mode", "supervised")
            task_type = ml_prep_results.get("task_type", "N/A")
            target = ml_prep_results.get("target_col", "N/A")
            scaler = ml_prep_results.get("numeric_scaler", "N/A")
            encoder = ml_prep_results.get("categorical_encoder", "N/A")
            leakage = ml_prep_results.get("leakage_warnings", [])

            leakage_html = ""
            if leakage:
                leak_items = "".join([f"<li><strong>{html.escape(l['column'])}</strong> : {html.escape(l['reason'])}</li>" for l in leakage])
                leakage_html = f"""
                <div class="alert alert-danger" style="margin-top: 15px;">
                    <strong>⚠️ Avertissements de Risque de Fuite de Données (Data Leakage) :</strong>
                    <ul>{leak_items}</ul>
                </div>
                """
            else:
                leakage_html = "<div class='alert alert-success' style='margin-top: 15px;'>✅ Aucun risque de fuite de données détecté.</div>"

            shape_info = ""
            if mode == "supervised":
                X_train = ml_prep_results["X_train"]
                X_test = ml_prep_results["X_test"]
                shape_info = f"<p><strong>Dimensions Train :</strong> {X_train.shape[0]} lignes × {X_train.shape[1]} variables | <strong>Test :</strong> {X_test.shape[0]} lignes × {X_test.shape[1]} variables</p>"
            else:
                X_prep = ml_prep_results.get("X_prepared")
                if X_prep is not None:
                    shape_info = f"<p><strong>Dimensions Préparées :</strong> {X_prep.shape[0]} lignes × {X_prep.shape[1]} variables</p>"

            ml_section_html = f"""
            <div class="card">
                <div class="card-body">
                    <p><strong>Mode :</strong> {html.escape(mode.capitalize())} | <strong>Tâche identifiée :</strong> <span class="badge badge-info">{html.escape(task_type)}</span></p>
                    <p><strong>Variable Cible :</strong> <code>{html.escape(target)}</code> | <strong>Stratégie de split :</strong> {html.escape(ml_prep_results.get("split_strategy", "N/A"))} (Test: {int(ml_prep_results.get("test_size", 0.2)*100)}%)</p>
                    <p><strong>Mise à l'échelle numérique :</strong> {html.escape(scaler.capitalize())} | <strong>Encodage catégoriel :</strong> {html.escape(encoder.capitalize())}</p>
                    {shape_info}
                    {leakage_html}
                </div>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>AutoDataPrep - Rapport d'Audit & Préparation des Données</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --border: #e2e8f0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 30px 40px;
            line-height: 1.5;
        }}
        .header {{
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            color: white;
            padding: 25px 30px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header h1 {{ margin: 0 0 8px 0; font-size: 26px; }}
        .header p {{ margin: 0; opacity: 0.9; font-size: 14px; }}
        .kpi-container {{
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }}
        .kpi-card {{
            flex: 1;
            min-width: 170px;
            background: var(--card-bg);
            padding: 18px 20px;
            border-radius: 10px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .kpi-title {{ font-size: 13px; color: #64748b; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
        .kpi-value {{ font-size: 24px; font-weight: 700; color: var(--text); }}
        .card {{
            background: var(--card-bg);
            border-radius: 10px;
            border: 1px solid var(--border);
            margin-bottom: 25px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            overflow: hidden;
        }}
        .card-header {{
            background: #f1f5f9;
            padding: 14px 20px;
            font-weight: 700;
            font-size: 16px;
            border-bottom: 1px solid var(--border);
            color: #0f172a;
        }}
        .card-body {{ padding: 20px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
        }}
        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background: #f8fafc;
            color: #475569;
            font-weight: 600;
        }}
        tr:hover {{ background-color: #f8fafc; }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 600;
        }}
        .badge-conf-élevée {{ background: #dcfce7; color: #15803d; }}
        .badge-conf-moyenne {{ background: #fef9c3; color: #a16207; }}
        .badge-conf-faible {{ background: #fee2e2; color: #b91c1c; }}
        .badge-danger {{ background: #fee2e2; color: #b91c1c; }}
        .badge-warning {{ background: #ffedd5; color: #c2410c; }}
        .badge-info {{ background: #e0f2fe; color: #0369a1; }}
        .badge-success {{ background: #dcfce7; color: #15803d; }}
        .alert {{
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 14px;
        }}
        .alert-danger {{ background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }}
        .alert-success {{ background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }}
        code {{
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: Consolas, Monaco, monospace;
            font-size: 12.5px;
            color: #d946ef;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
            margin-top: 30px;
        }}
    </style>
</head>
<body>

    <div class="header">
        <h1>Rapport d'Audit et de Préparation Machine Learning</h1>
        <p>Généré automatiquement par AutoDataPrep le {now_str} pour <strong>{html.escape(metadata.get("file_name", "Dataset"))}</strong></p>
    </div>

    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">Dimensions Initiales</div>
            <div class="kpi-value">{metadata.get("rows", 0)} × {metadata.get("cols", 0)}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Cellules Manquantes</div>
            <div class="kpi-value">{summary.get("total_missing_cells", 0)} ({metadata.get("missing_pct", 0)}%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Lignes Dupliquées</div>
            <div class="kpi-value">{summary.get("total_duplicates", 0)} ({summary.get("duplicate_pct", 0)}%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Mémoire Allouée</div>
            <div class="kpi-value">{metadata.get("memory_formatted", "0 Mo")}</div>
        </div>
    </div>

    <!-- Section 1 : Identification Sémantique des Variables -->
    <div class="card">
        <div class="card-header">1. Identification Sémantique et Caractéristiques des Variables</div>
        <div class="card-body" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Variable</th>
                        <th>Type Sémantique Détecté</th>
                        <th>Confiance</th>
                        <th>Manquantes</th>
                        <th>Distinctes</th>
                        <th>Problèmes Détectés</th>
                        <th>Recommandations</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(profiles_rows_html)}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Section 2 : Audit de Qualité Détaillé -->
    <div class="card">
        <div class="card-header">2. Audit de Qualité des Données (Problèmes Détectés)</div>
        <div class="card-body" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Variable</th>
                        <th>Problème</th>
                        <th>Gravité</th>
                        <th>Impact</th>
                        <th>Action Proposée</th>
                        <th>Justification Méthodologique</th>
                        <th>État</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(issues_rows_html)}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Section 3 : Journal des Opérations de Nettoyage Exécutées -->
    <div class="card">
        <div class="card-header">3. Opérations de Nettoyage Réellement Exécutées (Traçabilité)</div>
        <div class="card-body" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Horodatage</th>
                        <th>Opération</th>
                        <th>Colonne(s)</th>
                        <th>Stratégie</th>
                        <th>Détails & Impact</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(history_rows_html)}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Section 4 : Nouvelles Caractéristiques Créées -->
    <div class="card">
        <div class="card-header">4. Nouvelles Caractéristiques Créées (Feature Engineering)</div>
        <div class="card-body" style="padding: 0; overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Source</th>
                        <th>Colonnes Générées</th>
                        <th>Justification</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(feat_rows_html)}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Section 5 : Configuration et Pipeline Machine Learning -->
    <div class="card">
        <div class="card-header">5. Configuration & Pipeline Machine Learning (Garantie Zéro-Leakage)</div>
        <div class="card-body">
            {ml_section_html}
        </div>
    </div>

    <!-- Section 6 : Résultats Après Nettoyage -->
    <div class="card">
        <div class="card-header">6. Résultats Après Nettoyage & Impact des Opérations</div>
        <div class="card-body">
            <p><strong>Nombre total d'opérations de nettoyage exécutées :</strong> {len(cleaning_history)}</p>
            <p><strong>Impact sur la qualité des données :</strong></p>
            <ul style="margin-top: 10px; padding-left: 20px;">
                <li>Les opérations de nettoyage ont été appliquées séquentiellement avec traçabilité complète.</li>
                <li>Chaque opération a été justifiée méthodologiquement pour éviter les biais.</li>
                <li>Le journal des opérations permet de reproduire exactement le processus de préparation.</li>
            </ul>
            {f"<p style='margin-top: 15px; color: #16a34a;'><strong>✅ Nettoyage terminé avec succès.</strong> Les données sont prêtes pour l'analyse ou le Machine Learning.</p>" if cleaning_history else "<p style='margin-top: 15px; color: #64748b;'><em>Aucune opération de nettoyage n'a été exécutée. Les données sont dans leur état brut.</em></p>"}
        </div>
    </div>

    <div class="footer">
        AutoDataPrep © {datetime.now().year} — Conçu pour une préparation automatisée et rigoureuse des données en Data Science.
    </div>

</body>
</html>
"""
        report_path = self.output_dir / filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(report_path.resolve())

    def generate_markdown_report(
        self,
        metadata: Dict[str, Any],
        analysis_results: Dict[str, Any],
        cleaning_history: List[Dict[str, Any]],
        created_features: List[Dict[str, Any]],
        ml_prep_results: Optional[Dict[str, Any]] = None,
        filename: str = "rapport_preparation.md"
    ) -> str:
        """
        Generates a markdown (.md) report.
        """
        cleaning_history = [_normalize_dict_item(x) for x in (cleaning_history or [])]
        created_features = [_normalize_dict_item(x) for x in (created_features or [])]
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
        summary = analysis_results.get("summary", {})
        profiles = analysis_results.get("profiles", {})
        global_issues = analysis_results.get("global_issues", [])

        md = []
        md.append(f"# AutoDataPrep - Rapport d'Audit & Préparation des Données\n")
        md.append(f"**Dataset :** {metadata.get('file_name', 'N/A')}  ")
        md.append(f"**Date :** {now_str}  ")
        md.append(f"**Dimensions :** {metadata.get('rows', 0)} lignes × {metadata.get('cols', 0)} colonnes  ")
        md.append(f"**Mémoire approximative :** {metadata.get('memory_formatted', '0 Mo')}  \n")

        md.append("## 1. Caractéristiques Initiales & Identification Sémantique\n")
        md.append("| Variable | Type Sémantique | Confiance | Manquantes (%) | Distinctes (%) | Recommandation |")
        md.append("|---|---|---|---|---|---|")
        for col, prof in profiles.items():
            stats = prof["stats"]
            recs = prof["recommendations"][0]["action"] if prof["recommendations"] else "Conserver"
            md.append(f"| `{col}` | {prof['detected_type']} | {prof['confidence']} | {stats.get('missing_pct', 0)}% | {stats.get('unique_pct', 0)}% | {recs} |")
        md.append("\n")

        md.append("## 2. Audit de Qualité des Données\n")
        md.append("| Variable | Problème | Gravité | Action Proposée | État |")
        md.append("|---|---|---|---|---|")
        for issue in global_issues:
            md.append(f"| `{issue.get('variable')}` | {issue.get('issue')} | {issue.get('severity')} | {issue.get('action')} | {issue.get('status')} |")
        md.append("\n")

        md.append("## 3. Opérations de Nettoyage Exécutées\n")
        if cleaning_history:
            md.append("| Horodatage | Opération | Colonne | Stratégie | Détails |")
            md.append("|---|---|---|---|---|")
            for h in cleaning_history:
                md.append(f"| {h.get('timestamp')} | {h.get('operation')} | `{h.get('column')}` | {h.get('strategy')} | {h.get('details')} |")
        else:
            md.append("*Aucune opération de nettoyage manuelle exécutée.*")
        md.append("\n")

        md.append("## 4. Nouvelles Caractéristiques Créées\n")
        if created_features:
            md.append("| Type | Source | Nouvelles Colonnes | Justification |")
            md.append("|---|---|---|---|")
            for feat in created_features:
                md.append(f"| {feat.get('type')} | `{feat.get('source_column')}` | `{', '.join(feat.get('created_columns', []))}` | {feat.get('justification')} |")
        else:
            md.append("*Aucune nouvelle caractéristique créée.*")
        md.append("\n")

        md.append("## 5. Préparation Machine Learning\n")
        if ml_prep_results:
            md.append(f"- **Mode :** {ml_prep_results.get('mode')}")
            md.append(f"- **Tâche Détectée :** {ml_prep_results.get('task_type')}")
            md.append(f"- **Cible :** `{ml_prep_results.get('target_col', 'N/A')}`")
            md.append(f"- **Mise à l'échelle numérique :** {ml_prep_results.get('numeric_scaler')}")
            md.append(f"- **Encodage catégoriel :** {ml_prep_results.get('categorical_encoder')}")
            if ml_prep_results.get("mode") == "supervised":
                md.append(f"- **Taille Train/Test :** {ml_prep_results['X_train'].shape} / {ml_prep_results['X_test'].shape}")
        else:
            md.append("*Aucune configuration ML appliquée.*")
        md.append("\n")

        report_path = self.output_dir / filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))

        return str(report_path.resolve())

    def generate_word_report(
        self,
        metadata: Dict[str, Any],
        analysis_results: Dict[str, Any],
        cleaning_history: List[Dict[str, Any]],
        created_features: List[Dict[str, Any]],
        ml_prep_results: Optional[Dict[str, Any]] = None,
        filename: str = "rapport_preparation.docx"
    ) -> str:
        """
        Generates a Word (.docx) report with detailed explanations.
        """
        try:
            from docx import Document
            from docx.shared import Pt, RGBColor
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        except ImportError:
            raise ImportError("python-docx is required for Word export. Install with: pip install python-docx")

        doc = Document()
        cleaning_history = [_normalize_dict_item(x) for x in (cleaning_history or [])]
        created_features = [_normalize_dict_item(x) for x in (created_features or [])]
        
        # Title
        title = doc.add_heading('AutoDataPrep - Rapport d\'Audit & Préparation des Données', 0)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Metadata
        doc.add_heading('Informations Générales', level=1)
        p = doc.add_paragraph()
        p.add_run(f'Dataset : ').bold = True
        p.add_run(f"{metadata.get('file_name', 'N/A')}\n")
        p.add_run(f'Date : ').bold = True
        p.add_run(f"{datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
        p.add_run(f'Dimensions : ').bold = True
        p.add_run(f"{metadata.get('rows', 0)} lignes × {metadata.get('cols', 0)} colonnes\n")
        p.add_run(f'Mémoire : ').bold = True
        p.add_run(f"{metadata.get('memory_formatted', '0 Mo')}\n")
        
        summary = analysis_results.get("summary", {})
        profiles = analysis_results.get("profiles", {})
        global_issues = analysis_results.get("global_issues", [])
        
        # KPIs
        doc.add_heading('Indicateurs Clés de Performance', level=1)
        table = doc.add_table(rows=2, cols=4)
        table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Dimensions'
        hdr_cells[1].text = 'Manquantes'
        hdr_cells[2].text = 'Doublons'
        hdr_cells[3].text = 'Mémoire'
        row_cells = table.rows[1].cells
        row_cells[0].text = f"{metadata.get('rows', 0)} × {metadata.get('cols', 0)}"
        row_cells[1].text = f"{summary.get('total_missing_cells', 0)} ({metadata.get('missing_pct', 0)}%)"
        row_cells[2].text = f"{summary.get('total_duplicates', 0)} ({summary.get('duplicate_pct', 0)}%)"
        row_cells[3].text = f"{metadata.get('memory_formatted', '0 Mo')}"
        
        # Variable Profiles with detailed explanations
        doc.add_heading('1. Identification Sémantique des Variables', level=1)
        table = doc.add_table(rows=1, cols=7)
        table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Variable'
        hdr_cells[1].text = 'Type Sémantique'
        hdr_cells[2].text = 'Confiance'
        hdr_cells[3].text = 'Manquantes'
        hdr_cells[4].text = 'Distinctes'
        hdr_cells[5].text = 'Problèmes'
        hdr_cells[6].text = 'Recommandations'
        
        for col, prof in profiles.items():
            row_cells = table.add_row().cells
            row_cells[0].text = col
            row_cells[1].text = prof["detected_type"]
            
            # Add explanation for type detection
            type_explanation = prof.get("meta", {}).get("reason", "Analyse statistique")
            row_cells[1].add_paragraph(f"\nPourquoi : {type_explanation}", style='Intense Quote')
            
            row_cells[2].text = prof["confidence"]
            stats = prof["stats"]
            row_cells[3].text = f"{stats.get('missing_count', 0)} ({stats.get('missing_pct', 0)}%)"
            row_cells[4].text = f"{stats.get('unique_count', 0)} ({stats.get('unique_pct', 0)}%)"
            
            issues = ", ".join([i["issue"] for i in prof["issues"]]) if prof["issues"] else "Aucun"
            row_cells[5].text = issues
            
            # Detailed recommendations with justifications
            if prof["recommendations"]:
                rec_text = ""
                for rec in prof["recommendations"]:
                    rec_text += f"• {rec['action']}\n  Justification : {rec.get('justification', 'Amélioration qualité')}\n"
                row_cells[6].text = rec_text
            else:
                row_cells[6].text = "Conserver tel quel"
        
        # Quality Audit
        doc.add_page_break()
        doc.add_heading('2. Audit de Qualité des Données', level=1)
        table = doc.add_table(rows=1, cols=7)
        table.style = 'Light Grid Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Variable'
        hdr_cells[1].text = 'Problème'
        hdr_cells[2].text = 'Gravité'
        hdr_cells[3].text = 'Impact'
        hdr_cells[4].text = 'Action'
        hdr_cells[5].text = 'Justification'
        hdr_cells[6].text = 'État'
        
        for issue in global_issues:
            row_cells = table.add_row().cells
            row_cells[0].text = str(issue.get("variable", ""))
            row_cells[1].text = str(issue.get("issue", ""))
            row_cells[2].text = issue.get("severity", "Moyenne")
            row_cells[3].text = f"{issue.get('affected_count', 0)} ({issue.get('affected_pct', 0)}%)"
            row_cells[4].text = str(issue.get("action", ""))
            row_cells[5].text = str(issue.get("justification", ""))
            row_cells[6].text = issue.get("status", "À traiter")
        
        # Cleaning History with detailed explanations
        doc.add_page_break()
        doc.add_heading('3. Opérations de Nettoyage Exécutées', level=1)
        if cleaning_history:
            table = doc.add_table(rows=1, cols=5)
            table.style = 'Light Grid Accent 1'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = 'Horodatage'
            hdr_cells[1].text = 'Opération'
            hdr_cells[2].text = 'Colonne'
            hdr_cells[3].text = 'Stratégie'
            hdr_cells[4].text = 'Détails & Justification'
            
            for item in cleaning_history:
                row_cells = table.add_row().cells
                row_cells[0].text = item.get("timestamp", "")
                row_cells[1].text = item.get("operation", "")
                row_cells[2].text = item.get("column", "")
                row_cells[3].text = item.get("strategy", "")
                
                # Add explanation
                operation = item.get("operation", "").lower()
                explanation = ""
                if "imputation" in operation:
                    explanation = f"Remplacement des valeurs manquantes par {item.get('strategy', '')} pour préserver la distribution."
                elif "outlier" in operation:
                    explanation = f"Traitement des valeurs aberrantes ({item.get('strategy', '')}) pour réduire l'impact des points extrêmes."
                elif "duplicate" in operation:
                    explanation = "Suppression des doublons pour éviter le sur-apprentissage."
                elif "text" in operation:
                    explanation = "Normalisation du texte pour une meilleure cohérence."
                
                row_cells[4].text = f"{item.get('details', '')}\n\nPourquoi : {explanation}"
        else:
            doc.add_paragraph("Aucune opération de nettoyage exécutée.")
        
        # Results After Cleaning
        doc.add_page_break()
        doc.add_heading('6. Résultats Après Nettoyage', level=1)
        doc.add_paragraph(f"Nombre total d'opérations : {len(cleaning_history)}")
        doc.add_paragraph("Impact sur la qualité des données :")
        doc.add_paragraph("• Les opérations ont été appliquées séquentiellement avec traçabilité complète.", style='List Bullet')
        doc.add_paragraph("• Chaque opération a été justifiée méthodologiquement.", style='List Bullet')
        doc.add_paragraph("• Le journal permet de reproduire exactement le processus.", style='List Bullet')
        
        if cleaning_history:
            p = doc.add_paragraph("✅ Nettoyage terminé avec succès. Les données sont prêtes pour l'analyse ou le ML.")
            p.runs[0].font.color.rgb = RGBColor(22, 163, 74)
        else:
            doc.add_paragraph("Aucune opération de nettoyage exécutée. Données dans l'état brut.")
        
        # ML Configuration
        if ml_prep_results:
            doc.add_page_break()
            doc.add_heading('5. Configuration Machine Learning', level=1)
            doc.add_paragraph(f"Mode : {ml_prep_results.get('mode', 'N/A')}")
            doc.add_paragraph(f"Tâche détectée : {ml_prep_results.get('task_type', 'N/A')}")
            doc.add_paragraph(f"Variable cible : {ml_prep_results.get('target_col', 'N/A')}")
            doc.add_paragraph(f"Mise à l'échelle numérique : {ml_prep_results.get('numeric_scaler', 'N/A')}")
            doc.add_paragraph(f"Encodage catégoriel : {ml_prep_results.get('categorical_encoder', 'N/A')}")
            
            if ml_prep_results.get("leakage_warnings"):
                doc.add_paragraph("⚠️ Avertissements de fuite de données détectés :")
                for warning in ml_prep_results["leakage_warnings"]:
                    doc.add_paragraph(f"• {warning['column']} : {warning['reason']}", style='List Bullet')
            else:
                doc.add_paragraph("✅ Aucun risque de fuite de données détecté.")
        
        # Save
        report_path = self.output_dir / filename
        doc.save(str(report_path))
        return str(report_path.resolve())

    def generate_excel_report(
        self,
        metadata: Dict[str, Any],
        analysis_results: Dict[str, Any],
        cleaning_history: List[Dict[str, Any]],
        created_features: List[Dict[str, Any]],
        ml_prep_results: Optional[Dict[str, Any]] = None,
        filename: str = "rapport_preparation.xlsx"
    ) -> str:
        """
        Generates an Excel (.xlsx) report with detailed explanations per feature.
        """
        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils.dataframe import dataframe_to_rows
        except ImportError:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")

        wb = Workbook()
        cleaning_history = [_normalize_dict_item(x) for x in (cleaning_history or [])]
        created_features = [_normalize_dict_item(x) for x in (created_features or [])]
        
        # Sheet 1: Summary
        ws_summary = wb.active
        ws_summary.title = "Résumé"
        
        # Header
        ws_summary['A1'] = "AutoDataPrep - Rapport d'Audit & Préparation des Données"
        ws_summary['A1'].font = Font(size=16, bold=True)
        ws_summary['A2'] = f"Dataset : {metadata.get('file_name', 'N/A')}"
        ws_summary['A3'] = f"Date : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"
        ws_summary['A4'] = f"Dimensions : {metadata.get('rows', 0)} lignes × {metadata.get('cols', 0)} colonnes"
        ws_summary['A5'] = f"Mémoire : {metadata.get('memory_formatted', '0 Mo')}"
        
        summary = analysis_results.get("summary", {})
        ws_summary['A7'] = "Indicateurs Clés"
        ws_summary['A7'].font = Font(bold=True)
        ws_summary['A8'] = "Dimensions"
        ws_summary['B8'] = f"{metadata.get('rows', 0)} × {metadata.get('cols', 0)}"
        ws_summary['A9'] = "Cellules Manquantes"
        ws_summary['B9'] = f"{summary.get('total_missing_cells', 0)} ({metadata.get('missing_pct', 0)}%)"
        ws_summary['A10'] = "Lignes Dupliquées"
        ws_summary['B10'] = f"{summary.get('total_duplicates', 0)} ({summary.get('duplicate_pct', 0)}%)"
        
        # Sheet 2: Feature Analysis
        ws_features = wb.create_sheet("Analyse par Feature")
        profiles = analysis_results.get("profiles", {})
        
        # Headers
        headers = ["Variable", "Type Sémantique", "Confiance", "Manquantes", "Distinctes", "Problèmes Détectés", "Recommandations", "Justification"]
        for col, header in enumerate(headers, 1):
            cell = ws_features.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
        
        # Data
        row = 2
        for col, prof in profiles.items():
            ws_features.cell(row=row, column=1, value=col)
            ws_features.cell(row=row, column=2, value=prof["detected_type"])
            ws_features.cell(row=row, column=3, value=prof["confidence"])
            
            stats = prof["stats"]
            ws_features.cell(row=row, column=4, value=f"{stats.get('missing_count', 0)} ({stats.get('missing_pct', 0)}%)")
            ws_features.cell(row=row, column=5, value=f"{stats.get('unique_count', 0)} ({stats.get('unique_pct', 0)}%)")
            
            issues = ", ".join([i["issue"] for i in prof["issues"]]) if prof["issues"] else "Aucun"
            ws_features.cell(row=row, column=6, value=issues)
            
            # Recommendations with justifications
            if prof["recommendations"]:
                rec_text = ""
                for rec in prof["recommendations"]:
                    rec_text += f"{rec['action']}\nJustification: {rec.get('justification', 'Amélioration qualité')}\n"
                ws_features.cell(row=row, column=7, value=rec_text)
            else:
                ws_features.cell(row=row, column=7, value="Conserver tel quel")
            
            # Type detection reason
            type_explanation = prof.get("meta", {}).get("reason", "Analyse statistique")
            ws_features.cell(row=row, column=8, value=type_explanation)
            
            row += 1
        
        # Sheet 3: Cleaning Operations
        ws_cleaning = wb.create_sheet("Opérations de Nettoyage")
        headers = ["Horodatage", "Opération", "Colonne", "Stratégie", "Détails", "Justification"]
        for col, header in enumerate(headers, 1):
            cell = ws_cleaning.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
        
        row = 2
        for item in cleaning_history:
            operation = item.get("operation", "")
            strategy = item.get("strategy", "")
            
            # Explanation
            explanation = ""
            if "imputation" in operation.lower():
                explanation = f"Remplacement des valeurs manquantes par {strategy} pour préserver la distribution."
            elif "outlier" in operation.lower():
                explanation = f"Traitement des valeurs aberrantes ({strategy}) pour réduire l'impact des points extrêmes."
            elif "duplicate" in operation.lower():
                explanation = "Suppression des doublons pour éviter le sur-apprentissage."
            elif "text" in operation.lower():
                explanation = "Normalisation du texte pour une meilleure cohérence."
            
            ws_cleaning.cell(row=row, column=1, value=item.get("timestamp", ""))
            ws_cleaning.cell(row=row, column=2, value=operation)
            ws_cleaning.cell(row=row, column=3, value=item.get("column", ""))
            ws_cleaning.cell(row=row, column=4, value=strategy)
            ws_cleaning.cell(row=row, column=5, value=item.get("details", ""))
            ws_cleaning.cell(row=row, column=6, value=explanation)
            row += 1
        
        if not cleaning_history:
            ws_cleaning.cell(row=2, column=1, value="Aucune opération de nettoyage exécutée.")
        
        # Sheet 4: ML Configuration
        if ml_prep_results:
            ws_ml = wb.create_sheet("Configuration ML")
            ws_ml['A1'] = "Configuration Machine Learning"
            ws_ml['A1'].font = Font(bold=True, size=14)
            ws_ml['A3'] = "Mode"
            ws_ml['B3'] = ml_prep_results.get("mode", "N/A")
            ws_ml['A4'] = "Tâche détectée"
            ws_ml['B4'] = ml_prep_results.get("task_type", "N/A")
            ws_ml['A5'] = "Variable cible"
            ws_ml['B5'] = ml_prep_results.get("target_col", "N/A")
            ws_ml['A6'] = "Mise à l'échelle numérique"
            ws_ml['B6'] = ml_prep_results.get("numeric_scaler", "N/A")
            ws_ml['A7'] = "Encodage catégoriel"
            ws_ml['B7'] = ml_prep_results.get("categorical_encoder", "N/A")
            
            if ml_prep_results.get("leakage_warnings"):
                ws_ml['A9'] = "⚠️ Avertissements de fuite de données"
                ws_ml['A9'].font = Font(bold=True, color="FF0000")
                row = 10
                for warning in ml_prep_results["leakage_warnings"]:
                    ws_ml[f'A{row}'] = f"• {warning['column']}"
                    ws_ml[f'B{row}'] = warning['reason']
                    row += 1
        
        # Save
        report_path = self.output_dir / filename
        wb.save(str(report_path))
        return str(report_path.resolve())
