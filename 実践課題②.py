"""CSVファイルから参加者のスコアを読み込み、平均・最高点・最低点を算出して表示するプログラム。

対応するCSVフォーマット:
  縦持ち形式（1行1スコア、名前列とスコア列を含む）:
    名前,日付,科目,スコア
    田中,2024-09-01,数学,80
    田中,2024-09-01,英語,90

  横持ち形式（1人1行、複数スコア列）:
    名前,スコア1,スコア2,スコア3
    田中,80,90,70
"""

import csv
import sys
import statistics
from pathlib import Path

NAME_COLUMNS = {"名前", "氏名", "name"}
SCORE_COLUMNS = {"スコア", "得点", "点数", "score"}


def load_scores(csv_path: str) -> list[dict]:
    """CSVファイルを読み込み、参加者ごとのスコアリストを返す（縦持ち・横持ち両対応）"""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [h.strip() for h in next(reader)]
        rows = [row for row in reader if row]

    name_idx = next((i for i, h in enumerate(header) if h in NAME_COLUMNS), 0)
    score_idx = next((i for i, h in enumerate(header) if h in SCORE_COLUMNS), None)

    grouped: dict[str, list[float]] = {}

    if score_idx is not None:
        # 縦持ち形式: 名前列とスコア列を1組だけ使う
        for row in rows:
            name = row[name_idx]
            value = row[score_idx].strip()
            if value == "":
                continue
            grouped.setdefault(name, []).append(float(value))
    else:
        # 横持ち形式: 名前列以外の全列をスコアとして扱う
        for row in rows:
            name = row[name_idx]
            scores = [
                float(v) for i, v in enumerate(row) if i != name_idx and v.strip() != ""
            ]
            grouped.setdefault(name, []).extend(scores)

    participants = []
    for name, scores in grouped.items():
        if not scores:
            print(f"警告: '{name}' のスコアが見つからないためスキップします", file=sys.stderr)
            continue
        participants.append({"name": name, "scores": scores})

    return participants


def analyze(participants: list[dict]) -> list[dict]:
    """各参加者の平均・最高点・最低点を計算する"""
    results = []
    for p in participants:
        scores = p["scores"]
        results.append({
            "name": p["name"],
            "average": statistics.mean(scores),
            "max": max(scores),
            "min": min(scores),
        })
    return results


def display_results(results: list[dict]) -> None:
    """結果を表形式で見やすく表示する"""
    if not results:
        print("表示できるデータがありません。")
        return

    name_width = max(len("名前"), max(len(r["name"]) for r in results))

    header = f"{'名前':<{name_width}}  {'平均':>8}  {'最高点':>8}  {'最低点':>8}"
    print(header)
    print("-" * len(header))

    for r in results:
        print(f"{r['name']:<{name_width}}  {r['average']:>8.2f}  {r['max']:>8.1f}  {r['min']:>8.1f}")

    print("-" * len(header))

    overall_avg = statistics.mean(r["average"] for r in results)
    best = max(results, key=lambda r: r["average"])
    worst = min(results, key=lambda r: r["average"])

    print(f"全体平均: {overall_avg:.2f}")
    print(f"最高平均: {best['name']} ({best['average']:.2f})")
    print(f"最低平均: {worst['name']} ({worst['average']:.2f})")


def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "scores.csv"

    if not Path(csv_path).exists():
        print(f"エラー: ファイル '{csv_path}' が見つかりません。", file=sys.stderr)
        sys.exit(1)

    participants = load_scores(csv_path)
    results = analyze(participants)
    display_results(results)


if __name__ == "__main__":
    main()
