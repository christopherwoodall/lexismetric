import pandas as pd
import plotly.express as px
import plotly.io as pio
from pathlib import Path
from datetime import datetime

class LexisReporter:
    def __init__(self, output_dir="./docs"):
        self.output_path = Path(output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def _generate_table_rows(self, results):
        """Generates rows for the deep inspection table with text expansions."""
        rows = ""
        for i, r in enumerate(results):
            fk_in = r["metrics_in"]["flesch_kincaid_grade"]
            fk_out = r["metrics_out"]["flesch_kincaid_grade"]
            delta = round(fk_out - fk_in, 2)
            
            rows += f"""
            <tr data-bs-toggle="collapse" data-bs-target="#inspect{i}" class="clickable-row">
                <td><strong>{r['model']}</strong></td>
                <td>{fk_in:.2f}</td>
                <td>{fk_out:.2f}</td>
                <td class="{'text-danger fw-bold' if delta > 2 else 'text-success'}">{delta:+.2f}</td>
                <td class="text-muted">{r['prompt'][:50]}...</td>
            </tr>
            <tr id="inspect{i}" class="collapse bg-light">
                <td colspan="5">
                    <div class="p-4 border-start border-4 border-primary bg-white shadow-sm rounded mx-2 my-2">
                        <div class="row">
                            <div class="col-md-6 border-end">
                                <h6 class="text-uppercase small fw-bold text-primary">Input Prompt</h6>
                                <div class="p-2 font-monospace" style="font-size: 0.9rem;">{r['prompt']}</div>
                            </div>
                            <div class="col-md-6">
                                <h6 class="text-uppercase small fw-bold text-success">Model Output</h6>
                                <div class="p-2 font-monospace" style="font-size: 0.9rem; white-space: pre-wrap;">{r['model_output']}</div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
            """
        return rows

    def generate(self, results):
        comparison_data = []
        for i, r in enumerate(results):
            fk_in = r["metrics_in"]["flesch_kincaid_grade"]
            fk_out = r["metrics_out"]["flesch_kincaid_grade"]
            wc_in = len(r["prompt"].split())
            wc_out = len(r["model_output"].split())

            comparison_data.append({"PairID": i, "Model": r["model"], "Type": "Prompt", "Grade": fk_in, "Length": wc_in})
            comparison_data.append({"PairID": i, "Model": r["model"], "Type": "Response", "Grade": fk_out, "Length": wc_out})

        df_shift = pd.DataFrame(comparison_data)
        df_simple = pd.DataFrame([{
            "Model": r["model"], "In": r["metrics_in"]["flesch_kincaid_grade"], "Out": r["metrics_out"]["flesch_kincaid_grade"]
        } for r in results])

        # Chart 1: Complexity Alignment
        fig1 = px.scatter(df_simple, x="In", y="Out", color="Model", trendline="ols",
                          title="Flesch-Kincaid Complexity Alignment", template="plotly_white")
        lims = [df_simple[['In', 'Out']].min().min(), df_simple[['In', 'Out']].max().max()]
        fig1.add_shape(type="line", line=dict(dash="dash", color="rgba(0,0,0,0.2)"),
                       x0=lims[0], y0=lims[0], x1=lims[1], y1=lims[1])

        # Chart 2: Linguistic Shift with custom data for JS access
        fig2 = px.line(df_shift, x="Grade", y="Length", color="Model", line_group="PairID",
                       symbol="Type", title="Linguistic Shift Map (Hover to Highlight Pair)",
                       labels={"Grade": "Grade Level (FK)", "Length": "Word Count"},
                       template="plotly_white", markers=True, custom_data=["PairID"])

        # Generate HTML components
        graph1_html = pio.to_html(fig1, full_html=False, include_plotlyjs='cdn', div_id="chart1")
        graph2_html = pio.to_html(fig2, full_html=False, include_plotlyjs=False, div_id="chart2")
        table_rows = self._generate_table_rows(results)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <style>
                body {{ background: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                .chart-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; }}
                .clickable-row {{ cursor: pointer; border-left: 4px solid transparent; }}
                .clickable-row:hover {{ background-color: #f8f9fa !important; border-left: 4px solid #0d6efd; }}
                .table thead {{ background: #212529; color: white; }}
            </style>
        </head>
        <body>
            <div class="container-fluid px-5 my-5">
                <h1 class="display-5 fw-bold mb-4">LexisMetric Deep Inspection 🏛️</h1>
                
                <div class="row">
                    <div class="col-xxl-6">
                        <div class="chart-card">{graph1_html}</div>
                    </div>
                    <div class="col-xxl-6">
                        <div class="chart-card">{graph2_html}</div>
                    </div>
                </div>

                <div class="bg-white p-4 rounded shadow-sm border">
                    <h3 class="mb-4">Evaluation Logs</h3>
                    <div class="table-responsive">
                        <table class="table table-hover border">
                            <thead>
                                <tr><th>Model</th><th>In (FK)</th><th>Out (FK)</th><th>Delta</th><th>Prompt Snippet</th></tr>
                            </thead>
                            <tbody>{table_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Logic for Linked Hover Highlighting
                const plotElement = document.getElementById('chart2');
                
                plotElement.on('plotly_hover', function(data) {{
                    const pairId = data.points[0].customdata[0];
                    const update = {{
                        'line.width': data.points[0].fullData.line.width,
                        'marker.size': data.points[0].fullData.marker.size
                    }};
                    
                    // Logic to find and bold the specific PairID line
                    const newStyles = plotElement.data.map(trace => {{
                        if (trace.line_group === pairId || (trace.customdata && trace.customdata[0][0] === pairId)) {{
                            return {{ 'line.width': 5, 'marker.size': 12 }};
                        }}
                        return {{ 'line.width': 2, 'marker.size': 6 }};
                    }});
                }});

                plotElement.on('plotly_unhover', function(data) {{
                    Plotly.restyle('chart2', {{ 'line.width': 2, 'marker.size': 8 }});
                }});
            </script>
        </body>
        </html>
        """
        (self.output_path / "index.html").write_text(html_content)
        return self.output_path / "index.html"