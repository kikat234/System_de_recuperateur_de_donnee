from datetime import datetime
import json
class RecoveryLogger:
    def __init__(self, log_file="recovery_log.txt"):
        self.log_file = log_file
        self.logs = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
        return log_entry
    
    def get_logs(self):
        return "\n".join(self.logs)
    
    def export_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
