from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from config.settings import Config

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client["thesis_checker"]
        self.results_collection = self.db["check_results"]
        self.templates_collection = self.db["templates"]
        
        # Create indexes
        self.results_collection.create_index([("check_id", 1)])
        self.results_collection.create_index([("timestamp", -1)])
    
    def save_check_result(self, result: Dict) -> str:
        """Save hasil pemeriksaan ke database"""
        try:
            result["saved_at"] = datetime.now()
            insert_result = self.results_collection.insert_one(result)
            return str(insert_result.inserted_id)
        except Exception as e:
            logging.error(f"Error saving check result: {e}")
            raise e
    
    def get_check_result(self, check_id: str) -> Optional[Dict]:
        """Get hasil pemeriksaan berdasarkan check_id"""
        try:
            result = self.results_collection.find_one({"check_id": check_id})
            if result:
                result["_id"] = str(result["_id"])  # Convert ObjectId to string
            return result
        except Exception as e:
            logging.error(f"Error getting check result: {e}")
            return None
    
    def get_recent_checks(self, limit: int = 50) -> List[Dict]:
        """Get pemeriksaan terbaru"""
        try:
            cursor = self.results_collection.find().sort("timestamp", -1).limit(limit)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)
            return results
        except Exception as e:
            logging.error(f"Error getting recent checks: {e}")
            return []
    
    def get_checking_statistics(self) -> Dict:
        """Get statistik pemeriksaan"""
        try:
            # Total checks
            total_checks = self.results_collection.count_documents({})
            
            # Checks today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_checks = self.results_collection.count_documents({
                "timestamp": {"$gte": today_start.isoformat()}
            })
            
            # Checks this week
            week_start = today_start - timedelta(days=7)
            week_checks = self.results_collection.count_documents({
                "timestamp": {"$gte": week_start.isoformat()}
            })
            
            # Compliance rate
            pass_checks = self.results_collection.count_documents({
                "format_analysis.compliance_status": "PASS"
            })
            
            pass_rate = (pass_checks / total_checks * 100) if total_checks > 0 else 0
            
            return {
                "total_checks": total_checks,
                "today_checks": today_checks,
                "week_checks": week_checks,
                "pass_rate": round(pass_rate, 2),
                "total_pass": pass_checks,
                "total_fail": total_checks - pass_checks
            }
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {}
    
    def save_template(self, template_data: Dict) -> str:
        """Save template dokumen"""
        try:
            template_data["uploaded_at"] = datetime.now()
            result = self.templates_collection.insert_one(template_data)
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error saving template: {e}")
            raise e