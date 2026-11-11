#!/usr/bin/env python3
"""Sistem Pakar Identifikasi Awal Gangguan WiFi pada Windows.
Metode Forward Chaining. Seluruh fakta awal berasal dari input interaktif pengguna.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KB_PATH = BASE_DIR / "knowledge_base.json"


def load_knowledge_base():
    with KB_PATH.open("r", encoding="utf-8") as file:
        kb = json.load(file)
    for key in ("judul", "batas", "sumber", "pertanyaan", "aturan"):
        if key not in kb:
            raise ValueError(f"Bagian wajib '{key}' tidak ditemukan di knowledge_base.json")
    for rule in kb["aturan"]:
        if rule.get("mode") not in ("dan", "atau"):
            raise ValueError(f"Mode aturan {rule.get('id')} harus 'dan' atau 'atau'.")
        if rule.get("sumber") not in kb["sumber"]:
            raise ValueError(f"Sumber untuk aturan {rule.get('id')} tidak terdaftar.")
        if not rule.get("jika") or not rule.get("maka"):
            raise ValueError(f"Premis/kesimpulan aturan {rule.get('id')} tidak lengkap.")
    return kb


def ask_user(questions):
    """Mengumpulkan fakta awal dari jawaban pengguna, bukan dari skenario bawaan."""
    memory, answers = set(), {}
    print("\nJawab berdasarkan kondisi perangkat/jaringan yang sedang diperiksa.")
    print("Ketik y/ya untuk Ya atau t/tidak untuk Tidak.\n")
    for index, question in enumerate(questions, start=1):
        while True:
            answer = input(f"{index}. {question['teks']} (y/t): ").strip().lower()
            if answer in ("y", "ya", "t", "tidak"):
                is_yes = answer in ("y", "ya")
                answers[question["id"]] = is_yes
                if is_yes:
                    memory.add(question["id"])
                break
            print("Input tidak dikenali. Masukkan y/ya atau t/tidak.")
    return memory, answers


def infer_forward_chaining(kb, initial_facts):
    """Menambahkan kesimpulan aturan ke working memory sampai tidak ada aturan baru."""
    memory = set(initial_facts)
    fired_rules, produced_by = [], {}
    while True:
        applicable = []
        for rule in kb["aturan"]:
            if rule["maka"] in memory:
                continue
            conditions = rule["jika"]
            matched = (
                all(item in memory for item in conditions)
                if rule["mode"] == "dan"
                else any(item in memory for item in conditions)
            )
            if matched:
                applicable.append(rule)
        if not applicable:
            break
        rule = applicable[0]
        memory.add(rule["maka"])
        fired_rules.append(rule)
        produced_by[rule["maka"]] = rule
    return memory, fired_rules, produced_by


def explain_fact(fact, produced_by, kb, indent=0, visited=None):
    if visited is None:
        visited = set()
    prefix = " " * indent
    if fact in visited:
        print(f"{prefix}- {fact} (rujukan berulang dihentikan)")
        return
    visited.add(fact)
    rule = produced_by.get(fact)
    if rule is None:
        print(f"{prefix}- {fact} (fakta awal dari jawaban pengguna)")
        return
    source = kb["sumber"][rule["sumber"]]
    print(f"{prefix}- {fact} <- {rule['id']} [{rule['sumber']}]")
    print(f"{prefix}  Premis ({rule['mode']}):")
    for condition in rule["jika"]:
        explain_fact(condition, produced_by, kb, indent + 4, visited)
    print(f"{prefix}  Referensi: {source['penerbit']} - {source['judul']}")


def show_result(kb, initial_facts, answers):
    _, fired_rules, produced_by = infer_forward_chaining(kb, initial_facts)
    print("\n" + "=" * 72)
    print(kb["judul"])
    print("=" * 72)
    print("\nFakta awal yang masuk ke working memory:")
    if initial_facts:
        for fact in sorted(initial_facts):
            print(f"  - {fact}")
    else:
        print("  (Tidak ada fakta yang dijawab Ya.)")
    print("\nProses inferensi Forward Chaining:")
    if fired_rules:
        for index, rule in enumerate(fired_rules, start=1):
            print(f"  Langkah {index}: {rule['id']} -> {rule['maka']}")
    else:
        print("  Tidak ada aturan yang premisnya terpenuhi.")
    print("\nKesimpulan sistem:")
    if fired_rules:
        for rule in fired_rules:
            print(f"  * {rule['maka']}")
    else:
        print("  Sistem belum dapat menghasilkan kesimpulan berdasarkan jawaban yang diberikan.")
    print("\nPenjelasan / jejak aturan:")
    if fired_rules:
        for rule in fired_rules:
            print(f"\n  Kesimpulan: {rule['maka']}")
            explain_fact(rule["maka"], produced_by, kb, indent=4)
    else:
        print("  Tidak ada aturan yang aktif. Gejala yang diberikan belum memenuhi premis aturan.")
    print("\nBatas keberlakuan:")
    print("  " + kb["batas"])
    print("\nCatatan: hasil sistem merupakan saran pemeriksaan awal, bukan keputusan akhir.")
    print("=" * 72)


def main():
    try:
        kb = load_knowledge_base()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Gagal membaca basis pengetahuan: {error}")
        raise SystemExit(1)
    print("\n" + kb["judul"])
    print("Metode penalaran : Forward Chaining")
    print("Basis pengetahuan: knowledge_base.json")
    print(f"Jumlah aturan    : {len(kb['aturan'])}")
    print("\nProgram menerima fakta awal langsung dari jawaban pengguna.")
    initial_facts, answers = ask_user(kb["pertanyaan"])
    show_result(kb, initial_facts, answers)


if __name__ == "__main__":
    main()
