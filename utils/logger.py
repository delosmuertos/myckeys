import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Callable
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "AVERTISSEMENT"
    ERROR = "ERREUR"
    CRITICAL = "CRITIQUE"

class Logger:
    def __init__(self, log_file: str = "app.log", max_logs: int = 1000):
        self.logs = []
        self.log_file = log_file
        self.max_logs = max_logs
        self.callbacks = []  # Callbacks pour notifier d'autres modules
        
    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Ajoute un callback pour être notifié des nouveaux logs"""
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[str], None]) -> None:
        """Retire un callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    def _notify_callbacks(self, log_entry: str) -> None:
        """Notifie tous les callbacks d'un nouveau log"""
        for callback in self.callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                print(f"Erreur dans le callback de log: {e}")

    def log(self, message: str, level: LogLevel = LogLevel.INFO, source: str = "SYSTEM") -> None:
        """Ajoute un message au log avec niveau et source"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.value}] [{source}] {message}"
        
        # Ajout au log en mémoire
        self.logs.append({
            'timestamp': timestamp,
            'level': level.value,
            'source': source,
            'message': message,
            'full_entry': log_entry
        })
        
        # Limitation du nombre de logs en mémoire
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
            
        # Notification des callbacks
        self._notify_callbacks(log_entry)
        
        # Affichage console
        print(log_entry)

    def debug(self, message: str, source: str = "SYSTEM") -> None:
        """Log de niveau DEBUG"""
        self.log(message, LogLevel.DEBUG, source)

    def info(self, message: str, source: str = "SYSTEM") -> None:
        """Log de niveau INFO"""
        self.log(message, LogLevel.INFO, source)

    def warning(self, message: str, source: str = "SYSTEM") -> None:
        """Log de niveau WARNING"""
        self.log(message, LogLevel.WARNING, source)

    def error(self, message: str, source: str = "SYSTEM") -> None:
        """Log de niveau ERROR"""
        self.log(message, LogLevel.ERROR, source)

    def critical(self, message: str, source: str = "SYSTEM") -> None:
        """Log de niveau CRITICAL"""
        self.log(message, LogLevel.CRITICAL, source)

    def get_logs(self, level: Optional[LogLevel] = None, source: Optional[str] = None, 
                 limit: Optional[int] = None) -> List[Dict]:
        """Récupère les logs avec filtres optionnels"""
        filtered_logs = self.logs.copy()
        
        if level:
            filtered_logs = [log for log in filtered_logs if log['level'] == level.value]
            
        if source:
            filtered_logs = [log for log in filtered_logs if log['source'] == source]
            
        if limit:
            filtered_logs = filtered_logs[-limit:]
            
        return filtered_logs

    def get_logs_as_strings(self, level: Optional[LogLevel] = None, 
                           source: Optional[str] = None, limit: Optional[int] = None) -> List[str]:
        """Récupère les logs sous forme de chaînes de caractères"""
        logs = self.get_logs(level, source, limit)
        return [log['full_entry'] for log in logs]

    def get_recent_logs(self, count: int = 10) -> List[Dict]:
        """Récupère les logs les plus récents"""
        return self.logs[-count:] if self.logs else []

    def search_logs(self, keyword: str, case_sensitive: bool = False) -> List[Dict]:
        """Recherche des logs contenant un mot-clé"""
        if case_sensitive:
            return [log for log in self.logs if keyword in log['message']]
        else:
            return [log for log in self.logs if keyword.lower() in log['message'].lower()]

    def clear_logs(self) -> None:
        """Efface tous les logs en mémoire"""
        self.logs.clear()
        self.info("Tous les logs ont été effacés", "LOGGER")

    def save_logs_to_file(self, filename: Optional[str] = None) -> bool:
        """Sauvegarde les logs dans un fichier JSON"""
        try:
            filepath = filename or self.log_file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, ensure_ascii=False, indent=2)
            self.info(f"Logs sauvegardés dans {filepath}", "LOGGER")
            return True
        except Exception as e:
            self.error(f"Erreur lors de la sauvegarde des logs: {e}", "LOGGER")
            return False

    def load_logs_from_file(self, filename: Optional[str] = None) -> bool:
        """Charge les logs depuis un fichier JSON"""
        try:
            filepath = filename or self.log_file
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded_logs = json.load(f)
                self.logs.extend(loaded_logs)
                self.info(f"Logs chargés depuis {filepath}", "LOGGER")
                return True
            return False
        except Exception as e:
            self.error(f"Erreur lors du chargement des logs: {e}", "LOGGER")
            return False

    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur les logs"""
        if not self.logs:
            return {
                'total_logs': 0,
                'logs_by_level': {},
                'logs_by_source': {},
                'oldest_log': None,
                'newest_log': None
            }
            
        stats = {
            'total_logs': len(self.logs),
            'logs_by_level': {},
            'logs_by_source': {},
            'oldest_log': self.logs[0]['timestamp'],
            'newest_log': self.logs[-1]['timestamp']
        }
        
        # Comptage par niveau
        for log in self.logs:
            level = log['level']
            source = log['source']
            
            stats['logs_by_level'][level] = stats['logs_by_level'].get(level, 0) + 1
            stats['logs_by_source'][source] = stats['logs_by_source'].get(source, 0) + 1
            
        return stats

    def export_logs_csv(self, filename: str) -> bool:
        """Exporte les logs au format CSV"""
        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Level', 'Source', 'Message'])
                for log in self.logs:
                    writer.writerow([log['timestamp'], log['level'], log['source'], log['message']])
            self.info(f"Logs exportés en CSV: {filename}", "LOGGER")
            return True
        except Exception as e:
            self.error(f"Erreur lors de l'export CSV: {e}", "LOGGER")
            return False

# Instance globale du logger
global_logger = Logger()

def get_logger() -> Logger:
    """Retourne l'instance globale du logger"""
    return global_logger 