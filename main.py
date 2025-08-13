from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import os
from datetime import datetime
import uuid
from bson import ObjectId

from models.document_checker import ThesisFormatChecker
from utils.pdf_processor import PDFProcessor
from database.db_manager import DatabaseManager
from config.settings import Config

# Setup logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)
app.secret_key = "thesis_checker_secret_key_2024"

# Initialize components
checker = ThesisFormatChecker()
pdf_processor = PDFProcessor()
db_manager = DatabaseManager()

def convert_objectid(obj):
    if isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

@app.route("/")
def index():
    """Home page untuk upload dokumen"""
    return render_template("index.html")

@app.route("/admin")
def admin_dashboard():
    """Dashboard admin untuk melihat hasil pemeriksaan"""
    recent_checks = db_manager.get_recent_checks(limit=50)
    statistics = db_manager.get_checking_statistics()
    return render_template("admin.html", 
                         recent_checks=recent_checks,
                         statistics=statistics)

@app.route("/api/check-document", methods=["POST"])
def check_document():
    """API endpoint untuk memeriksa format dokumen"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or "document_base64" not in data:
            return jsonify({"error": "Missing document_base64 in request"}), 400
        
        student_info = data.get("student_info", {})
        document_base64 = data["document_base64"]
        
        # Generate unique filename
        check_id = str(uuid.uuid4())
        filename = f"thesis_{check_id}.pdf"
        
        logging.info(f"Processing document check {check_id}")
        
        # Convert base64 to PDF
        file_path = pdf_processor.base64_to_pdf(document_base64, filename)
        
        # Validate PDF
        validation_result = pdf_processor.validate_pdf_file(file_path)
        if not validation_result["is_valid_pdf"]:
            return jsonify({
                "error": "File PDF tidak valid atau rusak",
                "validation_details": validation_result
            }), 400
        
        # Extract text and metadata
        extracted_text, pdf_metadata = pdf_processor.extract_text_from_pdf(file_path)
        
        # Load template for comparison (optional)
        template_text = ""
        template_path = "reference_docs/template_ta.pdf"
        if os.path.exists(template_path):
            template_text, _ = pdf_processor.extract_text_from_pdf(template_path)
        
        # Analyze document format
        format_analysis = checker.analyze_document_structure(extracted_text)
        # Cek detail halaman/bagian bermasalah
        page_issues = checker.check_page_format(extracted_text, pdf_metadata, file_path=file_path)
        format_analysis["page_issues"] = page_issues
        
        # Compare with template if available
        template_comparison = {}
        if template_text:
            template_comparison = checker.compare_with_template(extracted_text, template_text)
        
        # Prepare result
        result = {
            "check_id": check_id,
            "timestamp": datetime.now().isoformat(),
            "student_info": student_info,
            "pdf_metadata": pdf_metadata,
            "validation_result": validation_result,
            "format_analysis": format_analysis,
            "template_comparison": template_comparison,
            "file_path": file_path
        }
        
        # Save to database
        db_manager.save_check_result(result)
        
        # Clean up uploaded file (optional)
        # os.remove(file_path)
        
        logging.info(f"Document check {check_id} completed successfully")
        
        # Convert ObjectId to string before returning
        result = convert_objectid(result)
        
        return jsonify({
            "success": True,
            "check_id": check_id,
            "result": result
        })
        
    except Exception as e:
        logging.error(f"Error in document checking: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/api/get-check-result/<check_id>", methods=["GET"])
def get_check_result(check_id):
    """Get hasil pemeriksaan berdasarkan check_id"""
    try:
        result = db_manager.get_check_result(check_id)
        if result:
            result = convert_objectid(result)
            return jsonify({"success": True, "result": result})
        else:
            return jsonify({"error": "Check result not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload-template", methods=["POST"])
def upload_template():
    """Upload template dokumen yang benar"""
    try:
        data = request.get_json()
        if "template_base64" not in data:
            return jsonify({"error": "Missing template_base64"}), 400
        
        # Save template
        template_path = pdf_processor.base64_to_pdf(
            data["template_base64"], 
            "template_ta.pdf"
        )
        
        # Move to reference directory
        import shutil
        final_path = "reference_docs/template_ta.pdf"
        os.makedirs("reference_docs", exist_ok=True)
        shutil.move(template_path, final_path)
        
        return jsonify({"success": True, "message": "Template uploaded successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)