"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly") -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — GPU Cost Optimization Report",
        "",
        f"**Period:** {period}<br>",
        f"**Baseline spend:** ${baseline_usd:,.0f}<br>",
        f"**Optimized spend:** ${optimized_usd:,.0f}<br>",
        f"**Projected savings:** ${savings:,.0f}  (**{pct:.0f}%**)",
        "",
        "## Savings by lever",
        "",
        "| Lever | Savings (USD) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            f"- Energy per query: {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Carbon per query: {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Cleanest region (lab carbon snapshot): {sustainability.get('best_region', 'n/a')}",
        ]
    lines += ["", "_Figures are June-2026 as-of snapshots; re-baseline before acting._"]
    return "\n".join(lines)


def savings_waterfall(levers: dict, path: str, baseline_usd: float | None = None) -> str:
    """Write a waterfall with four incremental levers and optional total bars."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [levers[n] for n in names]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    current = baseline_usd if baseline_usd is not None else sum(vals)
    labels = (["Baseline"] if baseline_usd is not None else []) + names
    if baseline_usd is not None:
        ax.bar(0, current, color="#2e548a")
        ax.text(0, current + 200, f"${current:,.0f}", ha="center", fontsize=9)
    offset = int(baseline_usd is not None)
    for i, value in enumerate(vals):
        next_value = current - value
        x = i + offset
        ax.bar(x, value, bottom=next_value, color="#32936f")
        ax.text(x, current + 200, f"-${value:,.0f}", ha="center", fontsize=9)
        ax.plot([x, x + 1], [next_value, next_value], color="#888888", linewidth=0.8)
        current = next_value
    if baseline_usd is not None:
        labels.append("Optimized")
        ax.bar(len(labels)-1, current, color="#2e548a")
        ax.text(len(labels)-1, current + 200, f"${current:,.0f}", ha="center", fontsize=9)
    ax.set_xticks(range(len(labels)), labels, rotation=18, ha="right")
    ax.set_ylim(0, (baseline_usd if baseline_usd is not None else sum(vals)) * 1.15)
    ax.set_ylabel("Projected spend (USD / month)")
    ax.set_title("NimbusAI lab scenario: baseline to optimized")
    ax.grid(axis="y", alpha=0.2)
    plt.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
