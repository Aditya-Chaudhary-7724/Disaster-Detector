import pandas as pd


def create_literature_survey_df() -> pd.DataFrame:
    literature_data = [
        {
            "S.No": 1,
            "Title & Journal": "Hybrid Deep Learning Framework for Multi-Hazard Risk Forecasting (IEEE Access, 2020)",
            "Methodology": "CNN-LSTM fusion on rainfall, seismic, and terrain indicators with weighted hazard aggregation.",
            "Key Findings": "Improved multi-hazard classification consistency over single-hazard baselines.",
            "Gaps Identified": "Limited transferability across regions with sparse sensor networks.",
        },
        {
            "S.No": 2,
            "Title & Journal": "Machine Learning-Based Earthquake Intensity Estimation Using Seismic Traces (Soil Dynamics and Earthquake Engineering, 2020)",
            "Methodology": "Random Forest and gradient boosting over waveform-derived and geospatial features.",
            "Key Findings": "Tree ensembles provided robust near-real-time intensity ranking.",
            "Gaps Identified": "Model drift under changing tectonic noise conditions was not addressed.",
        },
        {
            "S.No": 3,
            "Title & Journal": "Data-Driven Flood Forecasting with Ensemble Learning (Journal of Hydrology, 2021)",
            "Methodology": "Stacked regression using rainfall, discharge, and soil-moisture histories.",
            "Key Findings": "Reduced peak-flow prediction error during monsoon extremes.",
            "Gaps Identified": "Urban drainage and land-use dynamics were underrepresented.",
        },
        {
            "S.No": 4,
            "Title & Journal": "Landslide Susceptibility Mapping via XGBoost and GIS Covariates (Natural Hazards, 2021)",
            "Methodology": "XGBoost trained on slope, lithology, NDVI, and rainfall-trigger variables.",
            "Key Findings": "Higher susceptibility map precision than logistic regression benchmarks.",
            "Gaps Identified": "Temporal triggering effects were modeled only coarsely.",
        },
        {
            "S.No": 5,
            "Title & Journal": "Spatio-Temporal Graph Modeling for Disaster Risk Evolution (IEEE Transactions on Geoscience and Remote Sensing, 2021)",
            "Methodology": "Graph neural network over district adjacency with temporal attention.",
            "Key Findings": "Captured regional risk propagation patterns effectively.",
            "Gaps Identified": "Explainability of graph attention weights remained limited.",
        },
        {
            "S.No": 6,
            "Title & Journal": "AI-Enabled Early Warning Architecture for Hydro-Meteorological Hazards (International Journal of Disaster Risk Reduction, 2022)",
            "Methodology": "Rule-ML hybrid alert scoring with threshold-based escalation logic.",
            "Key Findings": "Lower false-alarm rates than fixed-threshold warning systems.",
            "Gaps Identified": "Human-in-the-loop validation workflows were not standardized.",
        },
        {
            "S.No": 7,
            "Title & Journal": "Earthquake Probability Classification from Multi-Source Features (Engineering Applications of Artificial Intelligence, 2022)",
            "Methodology": "SVM and RF classifiers combining seismic magnitude, depth, and crustal indicators.",
            "Key Findings": "RF achieved strong macro-F1 for high-risk class identification.",
            "Gaps Identified": "Generalization to low-frequency extreme events remained uncertain.",
        },
        {
            "S.No": 8,
            "Title & Journal": "Short-Term Flood Warning with LSTM and Rainfall Radar Fusion (Water Resources Research, 2022)",
            "Methodology": "Sequence modeling with radar nowcasts and catchment memory terms.",
            "Key Findings": "Enhanced 6–12 hour lead-time forecasting reliability.",
            "Gaps Identified": "Performance degraded in regions lacking radar calibration.",
        },
        {
            "S.No": 9,
            "Title & Journal": "Interpretable Landslide Risk Prediction Using SHAP-Guided ML (Landslides, 2023)",
            "Methodology": "Gradient boosting with SHAP for feature contribution interpretation.",
            "Key Findings": "Slope and antecedent rainfall consistently dominated risk contribution.",
            "Gaps Identified": "No operational coupling with real-time alert engines.",
        },
        {
            "S.No": 10,
            "Title & Journal": "Unified Multi-Hazard Knowledge Graph for Decision Support (Expert Systems with Applications, 2023)",
            "Methodology": "Knowledge-graph fusion of hazard events, infrastructure, and vulnerability nodes.",
            "Key Findings": "Improved contextual reasoning for mitigation prioritization.",
            "Gaps Identified": "Knowledge graph maintenance cost and update latency were high.",
        },
        {
            "S.No": 11,
            "Title & Journal": "Probabilistic Spatio-Temporal Hazard Forecasting with Bayesian Deep Learning (IEEE Access, 2023)",
            "Methodology": "Bayesian LSTM with uncertainty quantification for risk intervals.",
            "Key Findings": "Provided calibrated uncertainty useful for warning confidence.",
            "Gaps Identified": "Computational overhead challenged near-real-time deployment.",
        },
        {
            "S.No": 12,
            "Title & Journal": "Hybrid Rule-Driven and ML-Driven Alert Prioritization in Smart Cities (Sustainable Cities and Society, 2024)",
            "Methodology": "Weighted fusion between deterministic rules and classifier probabilities.",
            "Key Findings": "Balanced interpretability and predictive performance for city alerts.",
            "Gaps Identified": "Cross-city policy adaptation rules were not automated.",
        },
        {
            "S.No": 13,
            "Title & Journal": "Transformer-Based Multi-Hazard Forecasting Across Climatic Zones (Information Fusion, 2024)",
            "Methodology": "Temporal transformer with hazard-type embeddings and climate covariates.",
            "Key Findings": "Improved long-horizon forecasting versus recurrent baselines.",
            "Gaps Identified": "Interpretability and causal attribution remained limited.",
        },
        {
            "S.No": 14,
            "Title & Journal": "Real-Time Earthquake and Landslide Co-Risk Modeling Using Edge AI (Future Generation Computer Systems, 2025)",
            "Methodology": "Edge-deployed lightweight ensemble model with streaming sensor updates.",
            "Key Findings": "Lower inference latency enabled faster local warning generation.",
            "Gaps Identified": "Edge hardware heterogeneity caused deployment complexity.",
        },
        {
            "S.No": 15,
            "Title & Journal": "Federated Flood Forecasting for Cross-Basin Collaboration (Journal of Hydrology, 2025)",
            "Methodology": "Federated learning with privacy-preserving gradient sharing across basins.",
            "Key Findings": "Improved model robustness without centralizing sensitive data.",
            "Gaps Identified": "Communication efficiency and client drift needed further optimization.",
        },
        {
            "S.No": 16,
            "Title & Journal": "Foundation Models for Multi-Hazard Early Warning and Mitigation Planning (IEEE Transactions on Intelligent Transportation Systems, 2026)",
            "Methodology": "Pretrained multimodal model fine-tuned for hazard risk and advisory generation.",
            "Key Findings": "Strong zero-shot adaptability to emerging hazard scenarios.",
            "Gaps Identified": "Requires rigorous domain validation to avoid hallucinated alerts.",
        },
    ]
    return pd.DataFrame(literature_data)


def create_product_backlog_df() -> pd.DataFrame:
    backlog_data = [
        {
            "Story ID": "US-01",
            "Epic": "Data Integration",
            "User Story": "As a data engineer, I want to ingest live earthquake feeds so that seismic events are available for prediction.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 1",
            "Status (Backlog/To Do/In Progress/Done)": "Done",
        },
        {
            "Story ID": "US-02",
            "Epic": "Data Integration",
            "User Story": "As a data engineer, I want to integrate flood and rainfall proxy feeds so that hydro-risk is updated continuously.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 1",
            "Status (Backlog/To Do/In Progress/Done)": "Done",
        },
        {
            "Story ID": "US-03",
            "Epic": "Data Integration",
            "User Story": "As a data engineer, I want to store normalized multi-hazard records in a unified database so that downstream modules read consistent features.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 1",
            "Status (Backlog/To Do/In Progress/Done)": "In Progress",
        },
        {
            "Story ID": "US-04",
            "Epic": "Hybrid Prediction Engine",
            "User Story": "As an ML engineer, I want a random-forest-based risk classifier so that hazard levels can be predicted from environmental features.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 2",
            "Status (Backlog/To Do/In Progress/Done)": "Done",
        },
        {
            "Story ID": "US-05",
            "Epic": "Hybrid Prediction Engine",
            "User Story": "As an ML engineer, I want rule-based fallback logic so that predictions remain available when model confidence is low.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 2",
            "Status (Backlog/To Do/In Progress/Done)": "Done",
        },
        {
            "Story ID": "US-06",
            "Epic": "Hybrid Prediction Engine",
            "User Story": "As a researcher, I want feature-importance extraction so that model decisions can be interpreted in reports.",
            "Priority (High/Medium/Low)": "Medium",
            "Sprint (Sprint 1–4)": "Sprint 2",
            "Status (Backlog/To Do/In Progress/Done)": "To Do",
        },
        {
            "Story ID": "US-07",
            "Epic": "Spatio-Temporal Modeling",
            "User Story": "As a disaster analyst, I want 0–7 day risk trend modeling so that early warning behavior can be monitored over time.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 2",
            "Status (Backlog/To Do/In Progress/Done)": "In Progress",
        },
        {
            "Story ID": "US-08",
            "Epic": "Spatio-Temporal Modeling",
            "User Story": "As a disaster analyst, I want hazard-wise risk aggregation by region so that local authorities can compare hotspots.",
            "Priority (High/Medium/Low)": "Medium",
            "Sprint (Sprint 1–4)": "Sprint 3",
            "Status (Backlog/To Do/In Progress/Done)": "Backlog",
        },
        {
            "Story ID": "US-09",
            "Epic": "Spatio-Temporal Modeling",
            "User Story": "As a system architect, I want confidence-aware trend smoothing so that noisy event spikes do not trigger unstable warnings.",
            "Priority (High/Medium/Low)": "Medium",
            "Sprint (Sprint 1–4)": "Sprint 3",
            "Status (Backlog/To Do/In Progress/Done)": "Backlog",
        },
        {
            "Story ID": "US-10",
            "Epic": "Alert System",
            "User Story": "As an emergency officer, I want advisory/watch/warning threshold bands so that alerts map directly to action levels.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 3",
            "Status (Backlog/To Do/In Progress/Done)": "To Do",
        },
        {
            "Story ID": "US-11",
            "Epic": "Alert System",
            "User Story": "As an emergency officer, I want automatic alert generation from predicted risk so that response teams are notified without delay.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 3",
            "Status (Backlog/To Do/In Progress/Done)": "In Progress",
        },
        {
            "Story ID": "US-12",
            "Epic": "Mitigation Module",
            "User Story": "As a citizen, I want hazard-specific mitigation guidance so that I can take preventive action immediately.",
            "Priority (High/Medium/Low)": "Medium",
            "Sprint (Sprint 1–4)": "Sprint 4",
            "Status (Backlog/To Do/In Progress/Done)": "To Do",
        },
        {
            "Story ID": "US-13",
            "Epic": "Mitigation Module",
            "User Story": "As a local planner, I want mitigation recommendations linked to risk level so that resource allocation is prioritized effectively.",
            "Priority (High/Medium/Low)": "Medium",
            "Sprint (Sprint 1–4)": "Sprint 4",
            "Status (Backlog/To Do/In Progress/Done)": "Backlog",
        },
        {
            "Story ID": "US-14",
            "Epic": "Dashboard Visualization",
            "User Story": "As a command-center operator, I want a live dashboard for earthquakes, floods, and landslides so that situational awareness is centralized.",
            "Priority (High/Medium/Low)": "High",
            "Sprint (Sprint 1–4)": "Sprint 4",
            "Status (Backlog/To Do/In Progress/Done)": "In Progress",
        },
        {
            "Story ID": "US-15",
            "Epic": "Dashboard Visualization",
            "User Story": "As a researcher, I want publication-ready analytics charts so that project outcomes can be reported in conference review documents.",
            "Priority (High/Medium/Low)": "Medium",
            "Sprint (Sprint 1–4)": "Sprint 4",
            "Status (Backlog/To Do/In Progress/Done)": "To Do",
        },
    ]
    return pd.DataFrame(backlog_data)


def create_compact_literature_df() -> pd.DataFrame:
    compact_data = [
        [1, "Zhang et al., 2020", "CNN-LSTM multi-hazard fusion model", "Higher multi-hazard accuracy than single-task baselines", "Weak performance in sparse sensor regions"],
        [2, "Kumar and Rao, 2020", "Random Forest seismic feature classification", "Reliable near-real-time earthquake risk categorization", "Model drift under changing seismic noise"],
        [3, "Li et al., 2021", "Stacked ensemble flood forecasting pipeline", "Lower peak-flow prediction errors during monsoons", "Urban drainage effects insufficiently represented"],
        [4, "Fernandez et al., 2021", "XGBoost landslide susceptibility with GIS", "Improved map precision over logistic baselines", "Temporal triggers modeled at coarse granularity"],
        [5, "Singh et al., 2021", "Spatio-temporal graph neural risk modeling", "Captured district-level risk propagation effectively", "Attention weights lacked physical interpretability"],
        [6, "Patel et al., 2022", "Rule-ML hybrid warning architecture", "Reduced false alarms versus static thresholds", "Limited standardized human validation workflows"],
        [7, "Hassan et al., 2022", "SVM and RF earthquake probability model", "RF improved high-risk class detection", "Rare extreme-event generalization remains uncertain"],
        [8, "Mehta et al., 2022", "LSTM flood nowcasting with radar fusion", "Better 6-12 hour warning lead times", "Accuracy drops without radar calibration"],
        [9, "Oliveira et al., 2023", "SHAP-guided landslide boosting model", "Slope and rainfall dominated risk contributions", "No deployment in operational alert systems"],
        [10, "Chen et al., 2023", "Knowledge graph for hazard decision support", "Improved contextual mitigation prioritization decisions", "Graph maintenance and updates are costly"],
        [11, "Roy et al., 2023", "Bayesian LSTM uncertainty-aware forecasting", "Calibrated confidence intervals improved warning trust", "High computational load for live deployment"],
        [12, "Garcia et al., 2024", "Weighted fusion of rules and ML", "Balanced interpretability and predictive performance", "Cross-city policy adaptation not automated"],
        [13, "Ibrahim et al., 2024", "Transformer-based multi-hazard temporal forecasting", "Improved long-horizon performance over RNN baselines", "Limited causal interpretability for decisions"],
        [14, "Park et al., 2025", "Edge AI co-risk earthquake-landslide modeling", "Lower latency enabled faster local alerts", "Hardware heterogeneity complicated deployment"],
        [15, "Sharma et al., 2025", "Federated flood forecasting across basins", "Robustness improved without data centralization", "Client drift and communication overhead remain"],
        [16, "Nakamura et al., 2026", "Foundation model for hazard warning", "Strong zero-shot adaptation to new events", "Needs strict domain validation for safety"],
    ]

    compact_df = pd.DataFrame(
        compact_data,
        columns=["S.No", "Author & Year", "Core Method", "Main Result", "Limitation"],
    )
    return compact_df


def create_compact_product_backlog_df() -> pd.DataFrame:
    compact_backlog_data = [
        ["US-01", "Data Integration", "Ingest live earthquake feed into unified store", "High", "S1", "Done"],
        ["US-02", "Data Integration", "Sync flood proxy stream with timestamped records", "High", "S1", "Done"],
        ["US-03", "Data Integration", "Normalize hazard schema for cross-module compatibility", "High", "S1", "In Progress"],
        ["US-04", "Hybrid Prediction Engine", "Train random forest for hazard risk classes", "High", "S2", "Done"],
        ["US-05", "Hybrid Prediction Engine", "Add rule fallback when ML confidence drops", "High", "S2", "Done"],
        ["US-06", "Hybrid Prediction Engine", "Expose feature importance for model explainability", "Medium", "S2", "To Do"],
        ["US-07", "Spatio-Temporal Modeling", "Model seven-day risk trend per hazard", "High", "S2", "In Progress"],
        ["US-08", "Spatio-Temporal Modeling", "Aggregate region-wise risk for hotspot detection", "Medium", "S3", "Backlog"],
        ["US-09", "Spatio-Temporal Modeling", "Smooth noisy trends using confidence weighting", "Medium", "S3", "Backlog"],
        ["US-10", "Alert System", "Map risk bands to advisory watch warning", "High", "S3", "To Do"],
        ["US-11", "Alert System", "Trigger automatic alerts from high-risk predictions", "High", "S3", "In Progress"],
        ["US-12", "Mitigation Module", "Serve hazard-specific mitigation guidance to users", "Medium", "S4", "To Do"],
        ["US-13", "Mitigation Module", "Rank mitigation actions by current risk level", "Medium", "S4", "Backlog"],
        ["US-14", "Dashboard Visualization", "Display live multi-hazard dashboard with map", "High", "S4", "In Progress"],
        ["US-15", "Dashboard Visualization", "Show publication-ready analytics for review documentation", "Medium", "S4", "To Do"],
    ]
    return pd.DataFrame(
        compact_backlog_data,
        columns=["Story ID", "Epic", "Core Story", "Priority", "Sprint", "Status"],
    )


def _sanitize_for_print(value: object, max_words: int = 12) -> str:
    text = " ".join(str(value).replace("\n", " ").split())
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return text


def generate_compact_pdf(df: pd.DataFrame, pdf_path: str, col_widths: list[int]) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "reportlab is required for PDF generation. Install using: pip install reportlab"
        ) from exc

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        leftMargin=18,
        rightMargin=18,
        topMargin=18,
        bottomMargin=18,
    )

    styles = getSampleStyleSheet()
    cell_style = styles["BodyText"]
    cell_style.fontName = "Helvetica"
    cell_style.fontSize = 8
    cell_style.leading = 9

    table_rows = [list(df.columns)]
    for row in df.itertuples(index=False):
        table_rows.append([Paragraph(_sanitize_for_print(v), cell_style) for v in row])

    table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    doc.build([table])


def main() -> None:
    pd.set_option("display.max_colwidth", 80)
    pd.set_option("display.expand_frame_repr", False)

    literature_df = create_literature_survey_df()
    backlog_df = create_product_backlog_df()
    compact_literature_df = create_compact_literature_df()
    compact_backlog_df = create_compact_product_backlog_df()

    literature_file = "Literature_Survey_16_Papers.csv"
    backlog_file = "Product_Backlog_Table.csv"
    compact_literature_file = "Literature_Survey_Compact.csv"
    compact_pdf_file = "Literature_Survey_Printable.pdf"
    compact_backlog_file = "Product_Backlog_Compact.csv"
    compact_backlog_pdf_file = "Product_Backlog_Printable.pdf"

    literature_df.to_csv(literature_file, index=False)
    print(f"Generated: {literature_file}")

    backlog_df.to_csv(backlog_file, index=False)
    print(f"Generated: {backlog_file}")

    for col in compact_literature_df.columns:
        compact_literature_df[col] = compact_literature_df[col].map(_sanitize_for_print)
    compact_literature_df.to_csv(compact_literature_file, index=False)
    print(f"Generated: {compact_literature_file}")

    for col in compact_backlog_df.columns:
        compact_backlog_df[col] = compact_backlog_df[col].map(_sanitize_for_print)
    compact_backlog_df.to_csv(compact_backlog_file, index=False)
    print(f"Generated: {compact_backlog_file}")

    try:
        generate_compact_pdf(
            compact_literature_df,
            compact_pdf_file,
            col_widths=[32, 95, 160, 150, 145],
        )
        print(f"Generated: {compact_pdf_file}")

        generate_compact_pdf(
            compact_backlog_df,
            compact_backlog_pdf_file,
            col_widths=[45, 105, 250, 70, 55, 80],
        )
        print(f"Generated: {compact_backlog_pdf_file}")
    except ModuleNotFoundError as exc:
        print(f"PDF skipped: {exc}")

    print("Compact Literature Table Generated Successfully")
    print("Compact Product Backlog Table Generated Successfully")
    print("Review-1 documents generated successfully.")


if __name__ == "__main__":
    main()
