import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    
    # Document Format Rules
    REQUIRED_SECTIONS = [
        "HALAMAN JUDUL",
        "LEMBAR PENGESAHAN", 
        "ABSTRAK",
        "ABSTRACT",
        "KATA PENGANTAR",
        "DAFTAR ISI",
        "DAFTAR GAMBAR",
        "DAFTAR TABEL",
        "BAB I PENDAHULUAN",
        "BAB II TINJAUAN PUSTAKA",
        "BAB III METODOLOGI", 
        "BAB IV HASIL DAN PEMBAHASAN",
        "BAB V KESIMPULAN",
        "DAFTAR PUSTAKA",
        "LAMPIRAN"
    ]
    
    # Format Requirements
    FORMAT_RULES = {
        "font_size": {"min": 11, "max": 14, "recommended": 12},
        "line_spacing": {"required": "1.5 spasi"},
        "margin": {
            "top": "3 cm",
            "bottom": "3 cm", 
            "left": "4 cm",
            "right": "3 cm"
        },
        "page_numbers": {"required": True, "format": "angka"},
        "max_pages": {"undergraduate": 100, "master": 150, "phd": 200},
        "min_pages": {"undergraduate": 50, "master": 80, "phd": 120}
    }
    
    # LLM Prompts
    DOCUMENT_ANALYSIS_PROMPT = """
    Anda adalah sistem otomatis untuk memeriksa format dokumen tugas akhir mahasiswa.
    
    Analisis dokumen berikut dan periksa:
    1. Kelengkapan struktur BAB (I, II, III, IV, V)
    2. Keberadaan halaman wajib (Abstrak, Daftar Isi, dll)
    3. Format penomoran halaman
    4. Konsistensi penulisan judul BAB
    5. Struktur daftar pustaka
    
    Berikan penilaian dalam format JSON dengan field:
    - overall_score (0-100)
    - missing_sections (array)
    - format_issues (array)  
    - recommendations (array)
    - compliance_status (PASS/FAIL/NEEDS_REVISION)
    """