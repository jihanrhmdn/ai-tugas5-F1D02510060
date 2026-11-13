import sys
import textwrap
import json

LEBAR = 72

# Struktur data 
class Aturan:
    def __init__(self, id, mode, jika, maka, sumber):
        self.id = id
        self.mode = mode          # "dan" (semua syarat) atau "atau" (salah satu)
        self.jika = jika          # daftar syarat (list)
        self.maka = maka          # hasil kesimpulan
        self.sumber = sumber      # kode sumber referensi

    def terpenuhi(self, memori):
        """Apakah syarat aturan ini terpenuhi oleh fakta di memori?"""
        if self.mode == "dan":
            for s in self.jika:
                if s not in memori:
                    return False
            return True
        else: # mode "atau"
            for s in self.jika:
                if s in memori:
                    return True
            return False

    def syarat_terpakai(self, memori):
        """Syarat yang benar-benar ada di memori (untuk penjelasan/alasan)."""
        terpakai = []
        for s in self.jika:
            if s in memori:
                terpakai.append(s)
        return terpakai


class BasisPengetahuan:
    def __init__(self, judul, batas, sumber, aturan):
        self.judul = judul
        self.batas = batas
        self.sumber = sumber
        self.aturan = aturan


# Membaca file aturan berformat JSON
def baca_file(nama_file):
    with open(nama_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    aturan_list = []
    for item in data["aturan"]:
        aturan_list.append(Aturan(
            id=item["id"],
            mode=item["mode"],
            jika=item["jika"],
            maka=item["maka"],
            sumber=item["sumber"]
        ))
        
    return BasisPengetahuan(
        judul=data["judul"],
        batas=data["batas"],
        sumber=data["sumber"],
        aturan=aturan_list
    )


# Memisahkan fakta dasar (yang ditanyakan ke user) dan kesimpulan akhir
def pisahkan_fakta(kb):
    hasil = set()
    for a in kb.aturan:
        hasil.add(a.maka)

    syarat = []
    for a in kb.aturan:
        for s in a.jika:
            if s not in syarat:
                syarat.append(s)

    fakta_dasar = []
    for s in syarat:
        if s not in hasil:
            fakta_dasar.append(s)

    akhir = []
    for a in kb.aturan:
        if a.maka not in syarat and a.maka not in akhir:
            akhir.append(a.maka)

    return fakta_dasar, akhir


# Fungsi Tampilan & Layout Terminal
def garis(karakter="-"):
    print(karakter * LEBAR)


def judul_bagian(teks):
    print()
    garis("-")
    print(f" {teks}")
    garis("-")


def paragraf(teks, indent="  "):
    print(textwrap.fill(teks, width=LEBAR, initial_indent=indent, subsequent_indent=indent))


# Tanya jawab interaktif
def tanya(pertanyaan):
    while True:
        try:
            jawab = input(pertanyaan).strip().lower()
        except EOFError:
            return False
        if jawab in ("y", "ya"):
            return True
        if jawab in ("t", "tidak", "n"):
            return False
        print("    Jawab dengan y (ya) atau t (tidak).")


def kumpulkan_fakta(fakta_dasar):
    memori = []
    total = len(fakta_dasar)
    for no, f in enumerate(fakta_dasar, start=1):
        if tanya(f"[{no}/{total}] Apakah {f}? (y/t) > "):
            memori.append(f)
    return memori


# Mesin Forward Chaining
def forward_chaining(kb, memori):
    asal = {}
    siklus = 1
    while True:
        cocok = None
        for a in kb.aturan:
            if a.maka not in memori and a.terpenuhi(memori):
                cocok = a
                break

        if cocok is None:
            print(f"  Siklus {siklus}: tidak ada aturan baru, berhenti")
            return asal

        memori.append(cocok.maka)
        asal[cocok.maka] = cocok
        print(f"  Siklus {siklus}: {cocok.id}  ->  {cocok.maka}")
        siklus += 1


# Pelacakan Alasan Kesimpulan Secara Rekursif
def cetak_alasan(fakta, asal, memori, tingkat=1):
    aturan = asal.get(fakta)
    if aturan is None:  # Fakta dasar
        return

    pad = "   " * tingkat
    print(f"{pad}Aturan {aturan.id} [sumber: {aturan.sumber}], karena:")
    for s in aturan.syarat_terpakai(memori):
        print(f"{pad}  - {s}")
        cetak_alasan(s, asal, memori, tingkat + 2)


# Program Utama
def main():
    nama_file = sys.argv[1] if len(sys.argv) > 1 else "kb_lele.json"
    kb = baca_file(nama_file)
    fakta_dasar, kesimpulan_akhir = pisahkan_fakta(kb)

    garis("=")
    print(f" SISTEM PAKAR: {kb.judul}")
    garis("=")
    print(" Jawab setiap pertanyaan dengan y (ya) atau t (tidak).")
    print()

    memori = kumpulkan_fakta(fakta_dasar)

    judul_bagian("FAKTA AWAL")
    if memori:
        for f in memori:
            print(f"  - {f}")
    else:
        print("  (tidak ada)")

    judul_bagian("PROSES FORWARD CHAINING")
    asal = forward_chaining(kb, memori)

    ditemukan = []
    for k in kesimpulan_akhir:
        if k in memori:
            ditemukan.append(k)

    judul_bagian("KESIMPULAN")
    if not ditemukan:
        print("  Tidak ada kesimpulan dari fakta yang diberikan.")
    else:
        for no, k in enumerate(ditemukan, start=1):
            print(f"  {no}. {k}")

        judul_bagian("ALASAN")
        for no, k in enumerate(ditemukan, start=1):
            print(f" {no}. {k}")
            cetak_alasan(k, asal, memori)
            print()

    judul_bagian("CATATAN BATAS KEBERLAKUAN")
    paragraf(kb.batas)

    judul_bagian("SUMBER")
    for kode, ket in kb.sumber.items():
        print(textwrap.fill(f"{kode}: {ket}", width=LEBAR,
                            initial_indent="  ", subsequent_indent="       ", break_long_words=False, break_on_hyphens=False))
    print()
    garis("=")


if __name__ == "__main__":
    main()