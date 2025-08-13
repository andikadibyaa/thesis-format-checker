import logging
from typing import Dict, List, Tuple
from langchain_groq import ChatGroq
from config.settings import Config
import json
import re
import os
from utils.pdf_processor import PDFProcessor

class ThesisFormatChecker:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=Config.GROQ_API_KEY,
            model_name="llama3-70b-8192",
            temperature=0
        )
        self.required_sections = Config.REQUIRED_SECTIONS
        self.format_rules = Config.FORMAT_RULES
        
        # Load format guide JSON
        format_guide_path = os.path.join(os.path.dirname(__file__), "../reference_docs/format_guide.json")
        try:
            with open(format_guide_path, "r", encoding="utf-8") as f:
                self.format_guide = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load format_guide.json: {e}")
            self.format_guide = {}
        
    def analyze_document_structure(self, extracted_text: str) -> Dict:
        """Menganalisis struktur dokumen menggunakan LLM"""
        try:
            prompt = f"""
            {Config.DOCUMENT_ANALYSIS_PROMPT}
            
            DOKUMEN YANG DIANALISIS:
            {extracted_text[:8000]}  # Batasi untuk menghindari token limit
            
            BAGIAN WAJIB YANG HARUS ADA:
            {', '.join(self.required_sections)}
            """
            
            response = self.llm.invoke(prompt)
            
            # Parse response menjadi structured data
            analysis_result = self._parse_llm_response(response.content)
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"Error in LLM analysis: {e}")
            return self._fallback_analysis(extracted_text)
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse respons LLM menjadi struktur data"""
        try:
            # Coba extract JSON dari response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Pastikan semua field array ada
                data.setdefault("missing_sections", [])
                data.setdefault("format_issues", [])
                data.setdefault("recommendations", [])
                data.setdefault("overall_score", 0)
                data.setdefault("compliance_status", "PERLU_PERBAIKAN")
                return data
        except:
            pass
        
        # Fallback parsing manual
        return {
            "overall_score": self._extract_score(response),
            "missing_sections": [],
            "format_issues": [],
            "recommendations": [],
            "compliance_status": self._determine_compliance(response)
        }
    
    def _fallback_analysis(self, text: str) -> Dict:
        """Analisis fallback tanpa LLM, sesuai format_guide.json"""
        missing_sections = []
        found_sections = []

        # Gunakan required_sections dari format_guide jika ada
        required_sections = self.format_guide.get("required_sections", self.required_sections)
        text_upper = text.upper()

        for section in required_sections:
            if section.upper() in text_upper:
                found_sections.append(section)
            else:
                missing_sections.append(section)

        score = int((len(found_sections) / len(required_sections)) * 100)

        return {
            "overall_score": score,
            "missing_sections": missing_sections,
            "format_issues": self._check_basic_format_issues(text),
            "recommendations": self._generate_recommendations(missing_sections),
            "compliance_status": "LULUS" if score >= 80 else "PERLU_PERBAIKAN"
        }

    def _check_basic_format_issues(self, text: str) -> List[str]:
        """Periksa masalah format dasar sesuai format_guide.json"""
        issues = []
        format_rules = self.format_guide.get("format_rules", {})

        # Cek panjang dokumen
        min_pages = format_rules.get("min_pages", 50)
        pages_estimate = len(text) // 2000  # Estimasi kasar
        if pages_estimate < min_pages:
            issues.append(f"Dokumen terlalu pendek (kurang dari {min_pages} halaman)")

        # Cek struktur BAB
        bab_pattern = r'BAB\s+[IVX]+\s+'
        bab_matches = re.findall(bab_pattern, text.upper())
        if len(bab_matches) < 5:
            issues.append("Struktur BAB tidak lengkap (minimal 5 BAB)")

        # Cek daftar pustaka
        if "DAFTAR PUSTAKA" not in text.upper():
            issues.append("Daftar Pustaka tidak ditemukan")

        # Cek margin (tidak bisa otomatis, hanya reminder)
        margin = format_rules.get("margin", {})
        if margin:
            issues.append(
                f"Periksa margin: atas {margin.get('top')}, bawah {margin.get('bottom')}, kiri {margin.get('left')}, kanan {margin.get('right')}"
            )

        # Cek font size (tidak bisa otomatis, hanya reminder)
        font_size = format_rules.get("font_size", 12)
        issues.append(f"Pastikan ukuran font {font_size}pt")

        # Cek spasi (tidak bisa otomatis, hanya reminder)
        line_spacing = format_rules.get("line_spacing", "1.5")
        issues.append(f"Pastikan spasi {line_spacing}")

        return issues
    
    def compare_with_template(self, student_text: str, template_text: str) -> Dict:
        """Bandingkan dengan dokumen template"""
        prompt = f"""
        Bandingkan struktur dokumen mahasiswa dengan template yang benar.
        
        TEMPLATE YANG BENAR:
        {template_text[:4000]}
        
        DOKUMEN MAHASISWA:
        {student_text[:4000]}
        
        Berikan analisis perbandingan dan skor kemiripan struktur (0-100).
        """
        
        try:
            response = self.llm.invoke(prompt)
            return {"comparison_analysis": response.content}
        except Exception as e:
            return {"comparison_analysis": f"Error in comparison: {e}"}
    
    def _extract_score(self, text: str) -> int:
        """Extract score dari response text"""
        score_match = re.search(r'(\d+)(?:/100|%)', text)
        return int(score_match.group(1)) if score_match else 50
    
    def _extract_missing_sections(self, text: str) -> List[str]:
        """Extract missing sections dari response"""
        # Implementation untuk extract missing sections
        return []
    
    def _extract_format_issues(self, text: str) -> List[str]:
        """Extract format issues dari response"""
        # Implementation untuk extract format issues
        return []
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations dari response"""
        # Implementation untuk extract recommendations
        return []
    
    def _determine_compliance(self, text: str) -> str:
        """Determine compliance status"""
        if "PASS" in text.upper():
            return "PASS"
        elif "FAIL" in text.upper():
            return "FAIL"
        else:
            return "NEEDS_REVISION"
    
    def check_page_format(self, extracted_text: str, pdf_metadata: dict, file_path: str = None) -> List[dict]:
        issues = []
        # Cek jumlah halaman
        min_pages = self.format_guide.get("format_rules", {}).get("min_pages", 50)
        if pdf_metadata.get("total_pages", 0) < min_pages:
            issues.append({
                "page": "ALL",
                "issue": f"Jumlah halaman kurang dari {min_pages}"
            })
        # Cek bagian wajib
        required_sections = self.format_guide.get("required_sections", self.required_sections)
        for section in required_sections:
            if section.upper() not in extracted_text.upper():
                issues.append({
                    "section": section,
                    "issue": "Bagian tidak ditemukan"
                })
        # Cek posisi nomor halaman jika file_path diberikan
        if file_path:
            pdf_processor = PDFProcessor()
            positions = pdf_processor.detect_page_number_positions(file_path)
            # Ambil aturan posisi dari format_guide
            page_numbering_rules = self.format_guide.get("page_numbering_rules", {})
            allowed_positions = [
                page_numbering_rules.get("odd_position", "bottom-right"),
                page_numbering_rules.get("even_position", "bottom-left")
            ]
            for pos in positions:
                if pos["position"] not in allowed_positions:
                    issues.append({
                        "page": pos["page"],
                        "issue": f"Nomor halaman di posisi {pos['position']} (harusnya di {', '.join(allowed_positions)})"
                    })
        return issues