"""CSVファイルから参加者のスコアを読み込み、平均・最高点・最低点を算出して表示するプログラム。

対応するCSVフォーマット:
  縦持ち形式（1行1スコア、名前列とスコア列を含む）:
    名前,日付,科目,スコア
    田中,2024-09-01,数学,80
    田中,2024-09-01,英語,90

  横持ち形式（1人1行、複数スコア列）:
    名前,スコア1,スコア2,スコア3
    田中,80,90,70

  所属列がある場合は、所属（部署）ごとの集計も併せて表示・保存する:
    名前,所属,スコア
    田中,営業,80
"""

import csv
import sys
import statistics
from datetime import datetime
from pathlib import Path

NAME_COLUMNS = {"名前", "氏名", "name"}
SCORE_COLUMNS = {"スコア", "得点", "点数", "score"}
AFFILIATION_COLUMNS = {"所属", "部署", "department"}


def load_scores(csv_path: str) -> list[dict]:
    """CSVファイルを読み込み、参加者ごとのスコアリスト（所属があれば所属も）を返す（縦持ち・横持ち両対応）"""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [h.strip() for h in next(reader)]
        rows = [row for row in reader if row]

    name_idx = next((i for i, h in enumerate(header) if h in NAME_COLUMNS), 0)
    score_idx = next((i for i, h in enumerate(header) if h in SCORE_COLUMNS), None)
    affiliation_idx = next((i for i, h in enumerate(header) if h in AFFILIATION_COLUMNS), None)

    grouped: dict[str, list[float]] = {}
    affiliations: dict[str, str] = {}

    if score_idx is not None:
        # 縦持ち形式: 名前列とスコア列を1組だけ使う
        for row in rows:
            name = row[name_idx]
            value = row[score_idx].strip()
            if affiliation_idx is not None and name not in affiliations:
                affiliations[name] = row[affiliation_idx].strip()
            if value == "":
                continue
            grouped.setdefault(name, []).append(float(value))
    else:
        # 横持ち形式: 名前列・所属列以外の全列をスコアとして扱う
        skip_idx = {name_idx} | ({affiliation_idx} if affiliation_idx is not None else set())
        for row in rows:
            name = row[name_idx]
            if affiliation_idx is not None and name not in affiliations:
                affiliations[name] = row[affiliation_idx].strip()
            scores = [
                float(v) for i, v in enumerate(row) if i not in skip_idx and v.strip() != ""
            ]
            grouped.setdefault(name, []).extend(scores)

    participants = []
    for name, scores in grouped.items():
        if not scores:
            print(f"警告: '{name}' のスコアが見つからないためスキップします", file=sys.stderr)
            continue
        participants.append({
            "name": name,
            "scores": scores,
            "affiliation": affiliations.get(name),
        })

    return participants


def analyze(participants: list[dict]) -> list[dict]:
    """各参加者の平均・最高点・最低点を計算する"""
    results = []
    for p in participants:
        scores = p["scores"]
        results.append({
            "name": p["name"],
            "affiliation": p.get("affiliation"),
            "average": statistics.mean(scores),
            "max": max(scores),
            "min": min(scores),
        })
    return results


def analyze_by_affiliation(participants: list[dict]) -> list[dict]:
    """所属ごとの平均・最高点・最低点・人数を計算する（所属列がない場合は空リスト）"""
    grouped: dict[str, list[float]] = {}
    for p in participants:
        affiliation = p.get("affiliation")
        if not affiliation:
            continue
        grouped.setdefault(affiliation, []).extend(p["scores"])

    results = []
    for affiliation, scores in grouped.items():
        results.append({
            "affiliation": affiliation,
            "count": len(scores),
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


def display_affiliation_results(results: list[dict]) -> None:
    """所属ごとの集計結果を表形式で表示する"""
    if not results:
        return

    aff_width = max(len("所属"), max(len(r["affiliation"]) for r in results))

    print()
    header = f"{'所属':<{aff_width}}  {'人数':>6}  {'平均':>8}  {'最高点':>8}  {'最低点':>8}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['affiliation']:<{aff_width}}  {r['count']:>6}  {r['average']:>8.2f}  {r['max']:>8.1f}  {r['min']:>8.1f}")
    print("-" * len(header))


def save_results(results: list[dict], affiliation_results: list[dict], output_path: str) -> None:
    """集計結果をCSVファイルに保存する（所属別集計があれば併せて保存する）"""
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["名前", "平均", "最高点", "最低点"])
        for r in results:
            writer.writerow([r["name"], f"{r['average']:.2f}", r["max"], r["min"]])

        if affiliation_results:
            writer.writerow([])
            writer.writerow(["所属", "人数", "平均", "最高点", "最低点"])
            for r in affiliation_results:
                writer.writerow([r["affiliation"], r["count"], f"{r['average']:.2f}", r["max"], r["min"]])


def make_timestamped_filename() -> str:
    """実行日時を含む出力用ファイル名を生成する（例: results_20260924_2200.csv）"""
    return f"results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"


def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "scores.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else make_timestamped_filename()

    if not Path(csv_path).exists():
        print(f"エラー: ファイル '{csv_path}' が見つかりません。", file=sys.stderr)
        sys.exit(1)

    participants = load_scores(csv_path)
    results = analyze(participants)
    affiliation_results = analyze_by_affiliation(participants)
    display_results(results)
    display_affiliation_results(affiliation_results)

    save_results(results, affiliation_results, output_path)
    print(f"\n集計結果を '{output_path}' に保存しました。")


if __name__ == "__main__":
    main()
