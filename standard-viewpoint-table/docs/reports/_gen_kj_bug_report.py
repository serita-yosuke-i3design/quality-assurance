# -*- coding: utf-8 -*-
"""Issue export (CSV/TSV) -> single HTML bug analysis report.

DDP の工程順は「今回の結合テスト」の実施順に合わせる:
  ①デザインレビュー → ②探索的テスト → ③結合テスト → ④UAT
データ上「結合テストケース」「動作確認」は③に含める。
「単体テスト」「仕様/設計レビュー」等は①より上流として -1。
"""
import csv
import hashlib
import html
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_INPUT = Path(
    "/Users/serita.yosuke/Desktop/KJ_結合テスト_分析用_issues_全件_更新後 - KJ_結合テスト_分析用_issues_全件_更新後.csv"
)
HERE = Path(__file__).resolve().parent

SPECIAL_SKIP = {"バグではない", "検出不可", ""}
PHASE_ALIAS_FOR_INDEX = {"旧：仕様漏れ": "仕様/設計レビュー"}


def norm_for_phase_index(name: str) -> str:
    return PHASE_ALIAS_FOR_INDEX.get(name, name)


def phase_index(name: str) -> Optional[int]:
    """時系列インデックス（小さいほど上流）。比較不可は None。

    今回のテスト工程（ユーザー定義）:
      0=デザインレビュー, 1=探索的テスト, 2=結合テスト（+ケース+動作確認）, 3=UAT
    ①より前に最短が付く場合（単体・仕様レビュー等）: -1
    """
    raw = norm_for_phase_index((name or "").strip())
    if not raw or raw in SPECIAL_SKIP:
        return None
    if raw in ("仕様/設計レビュー", "単体テスト"):
        return -1
    if raw == "デザインレビュー":
        return 0
    if raw == "探索的テスト":
        return 1
    if raw in ("結合テスト", "結合テストケース", "動作確認"):
        return 2
    if raw == "UAT":
        return 3
    return None


def load_rows(path: Path) -> List[Dict[str, str]]:
    dialect = "excel-tab" if path.suffix.lower() == ".tsv" else "excel"
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, dialect=dialect):
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def is_defect_row(r: Dict[str, str]) -> bool:
    return (r.get("バグ分類") or "") != "バグではない"


def report_title_from_path(path: Path) -> str:
    name = path.name
    if "管理" in name and "EC" in name:
        return "KJ 結合テスト（EC・管理画面）— Issue 欠陥分析レポート"
    return "KJ 結合テスト分析用 Issues — 欠陥分析レポート"


def ddp_axis_sort_key(label: str) -> Tuple:
    display = label if label else "(空)"
    raw = label or ""
    idx = phase_index(raw)
    if idx is not None:
        return (0, idx, display)
    if not raw or raw in SPECIAL_SKIP:
        return (2, 99, display)
    return (1, 50, display)


def build_report(path_in: Path, path_out: Path, generated_on: date) -> None:
    rows = load_rows(path_in)
    sha = hashlib.sha256(path_in.read_bytes()).hexdigest()

    defect_rows = [r for r in rows if is_defect_row(r)]
    non_defect_n = len(rows) - len(defect_rows)
    n_def = len(defect_rows)

    gap_same = gap_late = gap_inconsistent = gap_missing = 0
    late_examples: List[Tuple[str, str, str]] = []
    inc_examples: List[Tuple[str, str, str]] = []
    for r in defect_rows:
        d = r.get("検出したテスト工程") or ""
        s = r.get("最短で検出できたテスト工程") or ""
        i_d = phase_index(d)
        i_s = phase_index(s)
        if i_d is None or i_s is None:
            gap_missing += 1
            continue
        if i_s < i_d:
            gap_late += 1
            if len(late_examples) < 4:
                late_examples.append((r.get("Title", "")[:90], d, s))
        elif i_s > i_d:
            gap_inconsistent += 1
            if len(inc_examples) < 5:
                inc_examples.append((r.get("Title", "")[:90], d, s))
        else:
            gap_same += 1

    status_c = Counter(r.get("Status") or "(空)" for r in defect_rows)
    bugcat_c = Counter(r.get("バグ分類") or "(空)" for r in defect_rows)
    reason_c = Counter(r.get("バグ発生理由") or "(空)" for r in defect_rows)
    det_c = Counter(r.get("検出したテスト工程") or "(空)" for r in defect_rows)
    short_c = Counter(r.get("最短で検出できたテスト工程") or "(空)" for r in defect_rows)
    prio_c = Counter(r.get("優先度") or "(空)" for r in defect_rows)

    retest = status_c.get("再テスト完了", 0)
    retest_rate = round(retest / n_def, 4) if n_def else 0.0

    retest_by_cat = Counter()
    for r in defect_rows:
        if r.get("Status") == "再テスト完了":
            retest_by_cat[r.get("バグ分類") or "(空)"] += 1

    cross: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in defect_rows:
        cross[r.get("バグ分類") or "(空)"][r.get("バグ発生理由") or "(空)"] += 1

    top_reasons = [k for k, _ in reason_c.most_common(8)]
    labels_bugcat = [k for k, _ in bugcat_c.most_common()]
    labels_reason = [k for k, _ in reason_c.most_common()]
    labels_det = [k for k, _ in det_c.most_common()]
    labels_short = [k for k, _ in short_c.most_common()]

    stack_labels = labels_bugcat[:15]
    other_cats = set(labels_bugcat[15:])
    stack_matrix: List[List[int]] = []
    for bc in labels_bugcat[:15]:
        stack_matrix.append([cross[bc][tr] for tr in top_reasons])
    if other_cats:
        oth = [0] * len(top_reasons)
        for bc in other_cats:
            for j, tr in enumerate(top_reasons):
                oth[j] += cross[bc][tr]
        stack_labels = stack_labels + ["（その他）"]
        stack_matrix.append(oth)

    empty_det = sum(1 for r in defect_rows if not (r.get("検出したテスト工程") or ""))
    empty_short = sum(1 for r in defect_rows if not (r.get("最短で検出できたテスト工程") or ""))
    empty_reason = sum(1 for r in defect_rows if not (r.get("バグ発生理由") or ""))

    pxc: Dict[str, Counter] = defaultdict(Counter)
    for r in defect_rows:
        pxc[r.get("優先度") or "(空)"][r.get("バグ分類") or "(空)"] += 1

    pair_c = Counter()
    for r in defect_rows:
        s_raw = r.get("最短で検出できたテスト工程") or ""
        d_raw = r.get("検出したテスト工程") or ""
        pair_c[(s_raw, d_raw)] += 1

    short_vals = sorted({s for s, _ in pair_c.keys()}, key=ddp_axis_sort_key)
    det_vals = sorted({d for _, d in pair_c.keys()}, key=ddp_axis_sort_key)

    def disp(lbl: str) -> str:
        return lbl if lbl else "(空)"

    def cell_style_and_title(s_raw: str, d_raw: str, n: int) -> Tuple[str, str]:
        if n == 0:
            return "ddp-empty", ""
        i_s = phase_index(s_raw)
        i_d = phase_index(d_raw)
        if i_s is None or i_d is None:
            return "ddp-na", "比較不可（空欄・検出不可・バグではない・未マップラベル等）"
        if i_s < i_d:
            depth = min(i_d - i_s, 7)
            return (
                f"ddp-late ddp-late-{depth}",
                f"左シフト余地: ①〜④の順で検出が{depth}段下流（{n}件）",
            )
        if i_s > i_d:
            return (
                "ddp-inc",
                "最短が検出より時系列で後ろ（ラベル意味・記録の見直し候補）",
            )
        return "ddp-same", "同一フェーズで検出"

    ddp_rows_html: List[str] = []
    ddp_rows_html.append(
        "<tr><th>最短 \\ 検出</th>"
        + "".join(f"<th>{html.escape(disp(d), quote=True)}</th>" for d in det_vals)
        + "<th class=\"ddp-marg\">行計</th></tr>"
    )
    late_pairs: List[Tuple[str, str, int]] = []
    for s in short_vals:
        row_cells: List[str] = []
        row_sum = 0
        for d in det_vals:
            n = pair_c[(s, d)]
            row_sum += n
            cls, ttl = cell_style_and_title(s, d, n)
            if n > 0:
                row_cells.append(
                    f"<td class=\"{cls}\" title=\"{html.escape(ttl, quote=True)}\"><b>{n}</b></td>"
                )
            else:
                row_cells.append(f"<td class=\"{cls}\">{n}</td>")
            i_s, i_d = phase_index(s), phase_index(d)
            if n and i_s is not None and i_d is not None and i_s < i_d:
                late_pairs.append((disp(s), disp(d), n))
        ddp_rows_html.append(
            f"<tr><th>{html.escape(disp(s), quote=True)}</th>"
            + "".join(row_cells)
            + f"<td class=\"ddp-marg\"><b>{row_sum}</b></td></tr>"
        )

    col_totals = [sum(pair_c[(s, d)] for s in short_vals) for d in det_vals]
    ddp_rows_html.append(
        "<tr><th class=\"ddp-marg\">列計</th>"
        + "".join(f"<td class=\"ddp-marg\"><b>{v}</b></td>" for v in col_totals)
        + f"<td class=\"ddp-marg\"><b>{sum(col_totals)}</b></td></tr>"
    )

    assert sum(pair_c.values()) == n_def

    late_pairs.sort(key=lambda x: -x[2])
    ddp_top_late_html = "<ol class=\"tight\">" + "".join(
        f"<li><code>{html.escape(s, quote=True)}</code> → 実際は <code>{html.escape(d, quote=True)}</code> で検出: <b>{n}</b>件</li>"
        for s, d, n in late_pairs[:12]
    ) + "</ol>"
    if not late_pairs:
        ddp_top_late_html = "<p>（該当セルなし）</p>"

    def esc(s: object) -> str:
        return html.escape(str(s), quote=True)

    reason_all = sorted({rr for bc in cross for rr in cross[bc]})
    bug_all = list(cross.keys())

    cross_rows_html: List[str] = []
    cross_rows_html.append(
        "<tr><th>バグ分類 \\ 理由</th>"
        + "".join(f"<th>{esc(r)}</th>" for r in reason_all)
        + "<th>計</th></tr>"
    )
    for bc in sorted(bug_all, key=lambda x: -sum(cross[x].values())):
        row_sum = sum(cross[bc][r] for r in reason_all)
        tds = "".join(f"<td>{cross[bc][r]}</td>" for r in reason_all)
        cross_rows_html.append(f"<tr><th>{esc(bc)}</th>{tds}<td><b>{row_sum}</b></td></tr>")

    prio_rows: List[str] = []
    for pr in sorted(pxc.keys(), key=lambda x: str(x)):
        sub = pxc[pr]
        top5 = sub.most_common(5)
        prio_rows.append(
            f"<tr><td>{esc(pr)}</td><td>{sum(sub.values())}</td><td>"
            + " / ".join(f"{esc(k)}({v})" for k, v in top5)
            + "</td></tr>"
        )

    analyzable = max(1, n_def - gap_missing)
    late_pct = round(100 * gap_late / analyzable, 1)

    top_cat, top_cat_n = bugcat_c.most_common(1)[0] if bugcat_c else ("(なし)", 0)
    det1, det1_n = det_c.most_common(1)[0] if det_c else ("(なし)", 0)
    det2 = det_c.most_common(2)[1] if len(det_c) >= 2 else None
    sh1, sh1_n = short_c.most_common(1)[0] if short_c else ("(なし)", 0)
    sh2 = short_c.most_common(2)[1] if len(short_c) >= 2 else None
    impl_n = reason_c.get("実装ミス", 0)
    unknown_n = reason_c.get("原因不明", 0)
    empty_reason_n = reason_c.get("(空)", 0)
    completed_n = status_c.get("完了", 0)

    retest_cat_line = "、".join(f"{esc(k)}が{v}件" for k, v in retest_by_cat.most_common(4)) or "（該当なし）"

    det_tail = f"、続いて「{esc(det2[0])}」{det2[1]}件" if det2 else ""
    sh_tail = f"、次点「{esc(sh2[0])}」{sh2[1]}件" if sh2 else ""

    reason_line = "、".join(
        [
            f"「実装ミス」{impl_n}件",
            f"「原因不明」{unknown_n}件",
            f"未記入（空欄）{empty_reason_n}件",
        ]
    )

    exec_html = f"""<p>欠陥レコードは <b>{n_def}件</b>（全体{len(rows)}件中、バグではない{non_defect_n}件を除く）。<b>バグ分類</b>では「{esc(top_cat)}」が最多（{top_cat_n}件）。<b>バグ発生理由</b>は{reason_line}。<b>検出したテスト工程</b>は「{esc(det1)}」{det1_n}件が中心{det_tail}。<b>最短で検出できたテスト工程</b>は「{esc(sh1)}」{sh1_n}件が最多{sh_tail}。DDP用の工程順は <strong>①デザインレビュー→②探索→③結合（結合テストケース・動作確認を含む）→④UAT</strong> とし、単体・仕様レビュー系は①より上流（インデックス-1）で比較。比較可能 {n_def - gap_missing} 件のうち <b>{gap_late}件（{late_pct}%）</b> は検出が最短より時系列で後ろ＝<strong>当該テストラインでの左シフト余地</strong>。検出工程空欄 <b>{empty_det}件</b>、最短空欄 <b>{empty_short}件</b>、理由空欄 <b>{empty_reason}件</b>。<b>Status</b> 完了{completed_n}件・再テスト完了{retest}件（{retest_rate * 100:.1f}%）。</p>"""

    empty_reason_pct = round(100 * empty_reason_n / n_def, 1) if n_def else 0.0
    analysis_reason = (
        f"<p>バグ発生理由の <b>{empty_reason_pct}%</b>（{empty_reason_n}/{n_def}件）が空欄のため、"
        "原因別の解釈は<strong>メタデータ整備</strong>が先になりうる。"
        f"記入がある範囲では実装ミス{impl_n}件、仕様不良{reason_c.get('仕様不良',0)}件、実装漏れ{reason_c.get('実装漏れ',0)}件など。</p>"
    )
    if unknown_n >= 15:
        analysis_reason += f"<p>「原因不明」が{unknown_n}件あり、調査未完のシグナルになりうる（推測）。</p>"

    analysis_ddp = f"""<p>今回の実施順（①デザイン→②探索→③結合→④UAT）に合わせると、検出の中心「{esc(det1)}」と最短の中心「{esc(sh1)}」の関係は、<strong>③④で取りこぼした想定のものが②で多く見えている</strong>等の読み方ができる（示唆・因果は断定しない）。集計上の検出遅延 {gap_late}件、最短と検出の順序が逆転している疑い {gap_inconsistent}件。</p>
<p><a href="#ddp-cross">「最短×検出」クロス表</a>の列は、上記①〜④（および比較外）に沿って並べている。<strong>セルが右（より後の工程）に寄るほど、最短で止められなかった分が後工程に流れた</strong>イメージ（左シフトの検討ポイント）。</p>"""

    follow_cats = bugcat_c.most_common(6)[1:6]
    follow_cat_str = "、".join(f"{k}（{v}件）" for k, v in follow_cats) if follow_cats else "—"

    analysis_style = ""
    if top_cat == "スタイル・レイアウト" or bugcat_c.get("スタイル・レイアウト", 0) >= 20:
        sl = bugcat_c.get("スタイル・レイアウト", 0)
        sl_empty = cross.get("スタイル・レイアウト", {}).get("(空)", 0)
        analysis_style = (
            f"<p>「スタイル・レイアウト」{sl}件規模のとき、受入基準とメタ記入が再テストと相関しやすい（参考）。理由未記入 {sl_empty}件。</p>"
        )

    analysis_status = (
        f"<p><strong>再テスト完了</strong>{retest}件（{retest_rate * 100:.1f}%）。内訳: {retest_cat_line}。</p>"
    )

    report = {
        "charts": {
            "bugcat": {"labels": labels_bugcat, "data": [bugcat_c[k] for k in labels_bugcat]},
            "reason": {"labels": labels_reason, "data": [reason_c[k] for k in labels_reason]},
            "det": {"labels": labels_det, "data": [det_c[k] for k in labels_det]},
            "short": {"labels": labels_short, "data": [short_c[k] for k in labels_short]},
            "status": {
                "labels": [k for k, _ in status_c.most_common()],
                "data": [v for _, v in status_c.most_common()],
            },
            "stack": {"labels": stack_labels, "reasons": top_reasons, "matrix": stack_matrix},
        },
        "gap": {
            "late_examples": [{"t": a, "det": b, "short": c} for a, b, c in late_examples],
            "inc_examples": [{"t": a, "det": b, "short": c} for a, b, c in inc_examples],
        },
    }
    report_json = json.dumps(report, ensure_ascii=False)

    inc_list = "".join(
        f"<li>{esc(x['t'])} — 検出:<code>{esc(x['det'])}</code> / 最短:<code>{esc(x['short'])}</code></li>"
        for x in report["gap"]["inc_examples"]
    )

    page_title = report_title_from_path(path_in)
    h1 = page_title

    html_doc = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg:#0f1419; --panel:#151b23; --text:#e6edf3; --muted:#8b949e; --border:#30363d; --accent:#58a6ff;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Hiragino Sans", sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }}
header {{ padding:1.5rem 1.25rem; border-bottom:1px solid var(--border); background:linear-gradient(180deg,#111821,#0f1419); }}
h1 {{ margin:0 0 .35rem; font-size:1.35rem; }}
h2 {{ margin:2rem 0 .75rem; font-size:1.1rem; color:#c9d1d9; border-bottom:1px solid var(--border); padding-bottom:.35rem; }}
h3 {{ margin:1rem 0 .5rem; font-size:.95rem; color:var(--accent); }}
h4 {{ margin:1.25rem 0 .5rem; font-size:.9rem; color:#8b949e; }}
main {{ max-width:1100px; margin:0 auto; padding:1rem 1.25rem 3rem; }}
#meta, #exec {{ background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:1rem 1.1rem; margin:1rem 0; }}
#meta code {{ color:#79c0ff; }}
.chart-wrap {{ background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:.75rem; margin:1rem 0; }}
.chart-wrap canvas {{ max-height:320px; }}
.sr-summary {{ font-size:.85rem; color:var(--muted); margin:.35rem 0 .75rem; }}
table.data {{ width:100%; border-collapse:collapse; font-size:.82rem; margin:1rem 0; display:block; max-height:480px; overflow:auto; }}
table.data thead {{ position:sticky; top:0; background:#1c2430; z-index:1; }}
table.data th, table.data td {{ border:1px solid var(--border); padding:.35rem .45rem; text-align:left; }}
table.data td {{ text-align:right; }}
table.data th:first-child, table.data td:first-child {{ text-align:left; position:sticky; left:0; background:#1c2430; }}
a {{ color:var(--accent); }}
.toc {{ font-size:.9rem; }}
.toc a {{ margin-right:.75rem; }}
.note {{ border-left:3px solid #d29922; padding:.5rem .75rem; background:#221c0f; color:#e3b341; font-size:.88rem; margin:1rem 0; }}
ul.tight li {{ margin:.25rem 0; }}
.ddp-legend {{ font-size:.82rem; color:var(--muted); margin:.75rem 0 1rem; display:flex; flex-wrap:wrap; gap:.75rem 1.25rem; align-items:center; }}
.ddp-legend span {{ display:inline-flex; align-items:center; gap:.35rem; }}
.ddp-swatch {{ width:14px; height:14px; border-radius:3px; border:1px solid var(--border); }}
table.ddp-matrix td, table.ddp-matrix th {{ text-align:center; min-width:2.5rem; }}
table.ddp-matrix th:first-child, table.ddp-matrix td:first-child {{ text-align:left; }}
.ddp-empty {{ color:#484f58; background:#0d1117; }}
.ddp-same {{ background:#1b4332; color:#d8f3dc; }}
.ddp-late-1 {{ background:#3d2f00; color:#ffe08a; }}
.ddp-late-2 {{ background:#5c3d00; color:#ffd; }}
.ddp-late-3 {{ background:#7a4a00; color:#fff; }}
.ddp-late-4 {{ background:#9c5c00; color:#fff; }}
.ddp-late-5 {{ background:#b86b00; color:#fff; }}
.ddp-late-6 {{ background:#d47800; color:#111; }}
.ddp-late-7 {{ background:#f08800; color:#111; }}
.ddp-inc {{ background:#3d1f4f; color:#e6d4ff; }}
.ddp-na {{ background:#21262d; color:#8b949e; }}
.ddp-marg {{ background:#161b22 !important; color:#c9d1d9; font-weight:600; }}
</style>
</head>
<body>
<header>
  <h1 id="top">{esc(h1)}</h1>
  <div class="toc">
    <a href="#meta">メタ</a>
    <a href="#exec">サマリー</a>
    <a href="#charts">グラフ</a>
    <a href="#ddp-cross">DDPクロス</a>
    <a href="#tables">集計表</a>
    <a href="#analysis">分析</a>
    <a href="#extra">付加分析</a>
    <a href="#ideas">参考改善案</a>
  </div>
</header>
<main>
<section id="meta">
  <h2>メタ情報</h2>
  <p>入力ファイル: <code>{esc(path_in.name)}</code>（{esc(path_in.suffix)}）</p>
  <p>全行数: <b>{len(rows)}</b> / 欠陥対象: <b>{n_def}</b> / 非欠陥: <b>{non_defect_n}</b></p>
  <p>SHA-256: <code>{sha}</code></p>
  <p>生成日: <b>{generated_on.isoformat()}</b></p>
  <p class="note"><strong>DDP用の時系列（今回のテスト実施順）</strong>: ①デザインレビュー(0) → ②探索的テスト(1) → ③結合テスト(2)（データ上の「結合テストケース」「動作確認」も③に含める）→ ④UAT(3)。単体テスト・仕様/設計レビュー（「旧：仕様漏れ」正規化後含む）は①より上流として -1。ギャップは「検出インデックス &gt; 最短インデックス」で左シフト余地。逆転はラベル意味の確認。組織の正式定義と異なる場合はマップを差し替えよ。</p>
</section>

<section id="exec">
  <h2>エグゼクティブサマリー</h2>
  {exec_html}
</section>

<section id="charts">
  <h2>可視化（Chart.js）</h2>
  <p class="sr-summary">各図の下に要約。CDN不可時は集計表で同値を確認。</p>
  <h3 id="c-bugcat">バグ分類（件数）</h3>
  <div class="chart-wrap"><canvas id="chartBugcat"></canvas></div>
  <p class="sr-summary">最多分類: {esc(top_cat)}（{top_cat_n}件）。</p>
  <h3 id="c-reason">バグ発生理由（件数）</h3>
  <div class="chart-wrap"><canvas id="chartReason"></canvas></div>
  <p class="sr-summary">空欄・実装ミス・仕様系の順で確認。</p>
  <h3 id="c-det">検出したテスト工程</h3>
  <div class="chart-wrap"><canvas id="chartDet"></canvas></div>
  <p class="sr-summary">最多: {esc(det1)}（{det1_n}件）。</p>
  <h3 id="c-short">最短で検出できたテスト工程</h3>
  <div class="chart-wrap"><canvas id="chartShort"></canvas></div>
  <p class="sr-summary">最多: {esc(sh1)}（{sh1_n}件）。</p>
  <h3 id="c-status">Status（欠陥のみ）</h3>
  <div class="chart-wrap"><canvas id="chartStatus"></canvas></div>
  <p class="sr-summary">完了・再テスト完了の比率。</p>
  <h3 id="c-stack">積み上げ棒：バグ分類 × バグ発生理由</h3>
  <div class="chart-wrap"><canvas id="chartStack"></canvas></div>
  <p class="sr-summary">分類ごとの理由内訳。</p>
</section>

<section id="tables">
  <h2>集計表</h2>
  <h3 id="ddp-cross">DDPモニタリング: 最短 × 検出（欠陥のみ）</h3>
  <p class="sr-summary">行＝最短、列＝検出。列は①→④の順（比較外は右端寄り）。</p>
  <div class="ddp-legend">
    <span><span class="ddp-swatch" style="background:#1b4332;"></span>同一フェーズ</span>
    <span><span class="ddp-swatch" style="background:#7a4a00;"></span>検出が時系列で後（左シフト余地）</span>
    <span><span class="ddp-swatch" style="background:#3d1f4f;"></span>最短の方が後（要確認）</span>
    <span><span class="ddp-swatch" style="background:#21262d;"></span>比較不可</span>
    <span><span class="ddp-swatch" style="background:#0d1117;"></span>0件</span>
  </div>
  <table class="data ddp-matrix">{"".join(ddp_rows_html)}</table>
  <h4>左シフト余地が大きい組み合わせ（件数上位）</h4>
  <p class="sr-summary">最短より検出が①〜④で後ろにあるセルから、件数多い順。</p>
  {ddp_top_late_html}

  <h3>バグ分類 × バグ発生理由（欠陥のみ）</h3>
  <table class="data">{"".join(cross_rows_html)}</table>

  <h3>優先度 × 件数・上位バグ分類（欠陥のみ）</h3>
  <table class="data">
    <thead><tr><th>優先度</th><th>件数</th><th>上位バグ分類（最多5）</th></tr></thead>
    <tbody>{"".join(prio_rows)}</tbody>
  </table>

  <h3>検出遅延サマリ（上記時系列に基づく）</h3>
  <table class="data">
    <tbody>
      <tr><th>同一フェーズで検出</th><td>{gap_same}</td></tr>
      <tr><th>検出が最短より時系列で後（左シフト余地）</th><td>{gap_late}</td></tr>
      <tr><th>最短が検出より後（定義・記録の見直し候補）</th><td>{gap_inconsistent}</td></tr>
      <tr><th>欠損・比較対象外</th><td>{gap_missing}</td></tr>
    </tbody>
  </table>
  <p>最短が検出より後ろに見える例（最大5件）:</p>
  <ul class="tight">{inc_list}</ul>
</section>

<section id="analysis">
  <h2>分析本文</h2>
  <h3>DDP／テスト工程（解釈）</h3>
  {analysis_ddp}
  <p>欠損 <b>{gap_missing}</b> 件は、検出・最短のいずれかが比較対象外または未マップ。</p>

  <h3>バグ分類（弱点の読み）</h3>
  <p>最多「{esc(top_cat)}」（{top_cat_n}件）。続く分類: {esc(follow_cat_str)} など。</p>
  {analysis_style}

  <h3>バグ発生理由と一般的開発との比較（定性）</h3>
  {analysis_reason}
  <p>メタ未記入が多いときは、業界比較以前に<strong>母数の歪み</strong>に注意（事実）。</p>

  <h3>Status（リワーク）</h3>
  {analysis_status}
</section>

<section id="extra">
  <h2>付加分析</h2>
  <ul class="tight">
    <li><b>優先度</b>: low {prio_c.get("low",0)} / medium {prio_c.get("medium",0)} / high {prio_c.get("high",0)} / 空欄 {prio_c.get("(空)",0)}。</li>
    <li><b>担当者</b>: 個人名集計は載せない。</li>
    <li><b>UAT検出</b> {det_c.get("UAT",0)} 件。最短が③以前なのに④で初見のセルは、<strong>結合〜③の厚み・データ</strong>の見直し候補になりうる（参考）。</li>
  </ul>
</section>

<section id="ideas">
  <h2>参考: 改善アイディア（未検証）</h2>
  <p class="note"><b>免責</b>: 要検証のうえ採用。</p>
  <ul class="tight">
    <li>起票テンプレで検出/最短を必須化し、本レポートの①〜④マップと整合させる。</li>
    <li>DDPクロスで濃いセル（②で見えたのに③④まで流れた等）から結合ケースを逆引き補強する。</li>
    <li>「旧：仕様漏れ」等を現行ラベルに統一する。</li>
    <li>再テスト多発分類向けに受入基準テンプレを先出しする。</li>
  </ul>
</section>

<footer style="margin-top:2rem;color:var(--muted);font-size:.82rem;">
  <p>Skill: <code>issue-bug-analysis-ddp-html</code>。DDPは検出vs最短のギャップ分析。</p>
</footer>
</main>

<script>
const REPORT = {report_json};

function barChart(id, labels, data, label, horizontal=true) {{
  const ctx = document.getElementById(id);
  new Chart(ctx, {{
    type: 'bar',
    data: {{ labels, datasets: [{{ label, data, backgroundColor: '#388bfd99', borderColor: '#388bfd', borderWidth: 1 }}]}},
    options: {{
      indexAxis: horizontal ? 'y' : 'x',
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }},
        y: {{ ticks: {{ color: '#8b949e', autoSkip: true, maxTicksLimit: 24 }}, grid: {{ display: false }} }}
      }}
    }}
  }});
}}

function doughnut(id, labels, data) {{
  const palette = ['#58a6ff','#3fb950','#d29922','#f85149','#a371f7','#79c0ff','#ff7b72','#56d364','#ffa657','#8b949e'];
  const ctx = document.getElementById(id);
  new Chart(ctx, {{
    type: 'doughnut',
    data: {{
      labels,
      datasets: [{{
        data,
        backgroundColor: labels.map((_,i)=>palette[i%palette.length]),
        borderColor: '#0f1419',
        borderWidth: 1
      }}]
    }},
    options: {{
      plugins: {{
        legend: {{ position: 'right', labels: {{ color: '#c9d1d9' }} }}
      }}
    }}
  }});
}}

const ch = REPORT.charts;
barChart('chartBugcat', ch.bugcat.labels, ch.bugcat.data, '件数', true);
barChart('chartReason', ch.reason.labels, ch.reason.data, '件数', true);
barChart('chartDet', ch.det.labels, ch.det.data, '件数', true);
barChart('chartShort', ch.short.labels, ch.short.data, '件数', true);
doughnut('chartStatus', ch.status.labels, ch.status.data);

const reasons = ch.stack.reasons;
const palette2 = ['#58a6ff','#8b949e','#d29922','#f85149','#3fb950','#a371f7','#79c0ff','#ffa657'];
const datasets = reasons.map((r, idx) => ({{
  label: r,
  data: ch.stack.matrix.map(row => row[idx]),
  backgroundColor: palette2[idx % palette2.length] + 'cc',
  borderColor: '#0f1419',
  borderWidth: 1
}}));
new Chart(document.getElementById('chartStack'), {{
  type: 'bar',
  data: {{ labels: ch.stack.labels, datasets }},
  options: {{
    responsive: true,
    scales: {{
      x: {{ stacked: true, ticks: {{ color: '#8b949e', maxRotation: 45, minRotation: 25 }} }},
      y: {{ stacked: true, beginAtZero: true, ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }}
    }},
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ color: '#c9d1d9', boxWidth: 12 }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    path_out.parent.mkdir(parents=True, exist_ok=True)
    path_out.write_text(html_doc, encoding="utf-8")
    print("Wrote", path_out, "bytes", path_out.stat().st_size)


def main() -> None:
    if len(sys.argv) >= 2:
        path_in = Path(sys.argv[1]).expanduser()
        if len(sys.argv) >= 3:
            path_out = Path(sys.argv[2]).expanduser()
        else:
            slug = path_in.stem.replace(" ", "-")[:80]
            path_out = HERE / f"{slug}-bug-analysis-report.html"
    else:
        path_in = DEFAULT_INPUT
        path_out = HERE / "kj-integration-issues-bug-analysis-report.html"
    if not path_in.is_file():
        raise SystemExit(f"Input not found: {path_in}")
    build_report(path_in, path_out, date(2026, 4, 24))


if __name__ == "__main__":
    main()
