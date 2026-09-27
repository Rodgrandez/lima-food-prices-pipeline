import re
from pathlib import Path

START, END = "<!-- STATUS:START -->", "<!-- STATUS:END -->"


def _movers(summary, n=5, ascending=False) -> str:
    s = summary.dropna(subset=["chg28"]).sort_values("chg28", ascending=ascending).head(n)
    return ", ".join(f"{r.variety} ({r.chg28:+.1f}%)" for r in s.itertuples())


def _count(n: int) -> str:
    return f"{n} {'variety' if n == 1 else 'varieties'}"


def status_markdown(status: dict, q: dict, summary) -> str:
    return "\n".join([
        (f"**Data through {status['last_date']}** (updated {status['updated_utc']}), {status['varieties']} active "
         "varieties at the Gran Mercado Mayorista de Lima."),
        "",
        (f"- Median 4-week price change: **{status['median_chg28']:+.1f}%**; diffusion (share rising >10% minus "
         f"share falling >10%): **{status['diffusion']:+.1f} pp**."),
        f"- Largest 4-week rises: {_movers(summary)}.",
        f"- Largest 4-week falls: {_movers(summary, ascending=True)}.",
        (f"- Data quality ({q['start']} to {q['end']}): {q['rows_clean']:,} clean observations, {q['duplicates']} "
         f"duplicates, {q['non_positive']} non-positive prices and {q['outliers']} outliers removed; median "
         f"coverage {q['coverage_median']:.0%}; {_count(len(q['stale_now']))} currently stale, "
         f"{len(q['discontinued'])} discontinued, {len(q['uncategorised'])} uncategorised."),
    ])


def update_readme(readme: Path, status: dict, q: dict, summary) -> None:
    text = Path(readme).read_text(encoding="utf-8")
    block = f"{START}\n{status_markdown(status, q, summary)}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.DOTALL)
    Path(readme).write_text(new, encoding="utf-8")
