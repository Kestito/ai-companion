import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class QALogger:
    def __init__(self, log_dir: str = "logs/qa_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("qa_logger")
        self.setup_logger()
        
    def setup_logger(self):
        """Setup logging configuration"""
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logging
        log_file = self.log_dir / f"qa_log_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
    def log_interaction(self, 
                       question: str, 
                       answer: str, 
                       is_rag: bool, 
                       metadata: Dict[str, Any] = None):
        """Log a single Q&A interaction"""
        timestamp = datetime.now().isoformat()
        
        interaction = {
            "timestamp": timestamp,
            "question": question,
            "answer": answer,
            "used_rag": is_rag,
            "metadata": metadata or {}
        }
        
        # Log to file
        self.logger.info(json.dumps(interaction, ensure_ascii=False))
        
        # Also save to JSON file for easier analysis
        json_file = self.log_dir / f"qa_data_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
                
            data.append(interaction)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
    
    def log_conversation(self, 
                        messages: list, 
                        metadata: Dict[str, Any] = None):
        """Log a conversation thread"""
        timestamp = datetime.now().isoformat()
        
        conversation = {
            "timestamp": timestamp,
            "messages": messages,
            "metadata": metadata or {}
        }
        
        # Log to conversation-specific JSON file
        conv_file = self.log_dir / f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving conversation: {e}")
    
    def get_qa_statistics(self) -> Dict[str, Any]:
        """Get statistics about Q&A interactions"""
        try:
            json_files = list(self.log_dir.glob("qa_data_*.json"))
            total_interactions = 0
            rag_interactions = 0
            questions = []
            
            for file in json_files:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_interactions += len(data)
                    rag_interactions += sum(1 for item in data if item["used_rag"])
                    questions.extend([item["question"] for item in data])
            
            return {
                "total_interactions": total_interactions,
                "rag_interactions": rag_interactions,
                "non_rag_interactions": total_interactions - rag_interactions,
                "rag_percentage": (rag_interactions / total_interactions * 100) if total_interactions > 0 else 0,
                "unique_questions": len(set(questions))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {} 