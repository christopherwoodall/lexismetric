import pandas as pd
import plotly.io as pio
import plotly.express as px
from pathlib import Path
from datetime import datetime


class LexisReporter:
    def __init__(self, output_dir="./docs"):
        self.output_path = Path(output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def _calculate_stats(self, df):
        """Calculates per-model performance and alignment metrics."""
        stats_html = ""
        # We focus correlation on the primary Flesch-Kincaid Grade
        for model in df["Model"].unique():
            subset = df[df["Model"] == model]
            if len(subset) > 1:
                correlation = subset["fk_grade_in"].corr(subset["fk_grade_out"])
                avg_shift = (subset["fk_grade_out"] - subset["fk_grade_in"]).mean()

                stats_html += f"""
                <div class="col-md-4">
                    <div class="card mb-3 border-0 shadow-sm">
                        <div class="card-body">
                            <h6 class="text-uppercase text-muted small fw-bold">{model}</h6>
                            <h3 class="card-title">{correlation:.2f}</h3>
                            <p class="card-text small">Pearson Correlation (Alignment)</p>
                            <hr>
                            <p class="mb-0"><strong>Avg Grade Shift:</strong> {avg_shift:+.2f}</p>
                        </div>
                    </div>
                </div>
                """
        return stats_html

    def generate(self, results):
        flat_data = []
        for r in results:
            row = {
                "Timestamp": r["timestamp"],
                "Model": r["model"],
                "Prompt Snippet": r["prompt"][:50] + "...",
            }
            # Dynamically flatten all metrics_in and metrics_out
            for m_name, m_val in r["metrics_in"].items():
                # Shorten keys for table headers (e.g., fk_grade_in)
                short_key = m_name.replace("flesch_kincaid_grade", "fk_grade")
                row[f"{short_key}_in"] = m_val

            for m_name, m_val in r["metrics_out"].items():
                short_key = m_name.replace("flesch_kincaid_grade", "fk_grade")
                row[f"{short_key}_out"] = m_val

            flat_data.append(row)

        df = pd.DataFrame(flat_data)

        # Create Visualization - Using Flesch-Kincaid as the primary anchor
        fig = px.scatter(
            df,
            x="fk_grade_in",
            y="fk_grade_out",
            color="Model",
            trendline="ols",
            title="Linguistic Complexity Parity (Flesch-Kincaid)",
            template="plotly_white",
            labels={
                "fk_grade_in": "Input Grade Level",
                "fk_grade_out": "Output Grade Level",
            },
        )

        # Add the Parity Line
        max_v = max(df["fk_grade_in"].max(), df["fk_grade_out"].max())
        min_v = min(df["fk_grade_in"].min(), df["fk_grade_out"].min())
        fig.add_shape(
            type="line",
            line=dict(dash="dash", color="rgba(0,0,0,0.2)"),
            x0=min_v,
            y0=min_v,
            x1=max_v,
            y1=max_v,
        )

        graph_html = pio.to_html(fig, full_html=False, include_plotlyjs="cdn")

        # Table with all columns
        table_html = df.to_html(
            classes="table table-sm table-striped small-text",
            index=False,
            border=0,
            justify="left",
        )

        stats_cards = self._calculate_stats(df)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>LexisMetric Deep Analytics</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <style>
                body {{ background-color: #f8f9fa; color: #333; }}
                .container-fluid {{ padding: 40px; }}
                .card {{ border-radius: 10px; }}
                .table-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow-x: auto; }}
                .small-text {{ font-size: 0.8rem; white-space: nowrap; }}
                h1 {{ font-weight: 800; letter-spacing: -1px; }}
                .parity-note {{ font-size: 0.85rem; color: #666; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="mb-5">
                    <h1>LexisMetric Deep Analytics 🏛️</h1>
                    <p class="text-muted">Multi-Dimensional Linguistic Evaluation | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                
                <div class="row mb-5">
                    {stats_cards}
                </div>

                <div class="card border-0 shadow-sm mb-5">
                    <div class="card-body">
                        {graph_html}
                        <p class="parity-note text-center mt-2">Dashed line represents perfect complexity parity (Input Level = Output Level).</p>
                    </div>
                </div>

                <div class="table-container">
                    <h4 class="mb-4">Full Dimensional Metric Logs</h4>
                    {table_html}
                </div>
            </div>
        </body>
        </html>
        """

        output_file = self.output_path / "index.html"
        output_file.write_text(html_content)
        return output_file
