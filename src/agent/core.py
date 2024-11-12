# src/agent/core.py
import yaml
import logging
from pathlib import Path
import sqlite3
from datetime import datetime
import psutil
import time

class NightMother:
    def __init__(self, config_path="config/config.yaml"):
        print("Initializing NightMother...")  # Debug line
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._init_database()
        self.logger.info("NightMother initialized")

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                print(f"Loaded config: {config}")  # Debug line
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            raise

    def _setup_logging(self):
        log_path = Path(self.config['logging']['file'])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add console handler for immediate feedback
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_path)),
                logging.StreamHandler()  # This will print to console
            ]
        )
        self.logger = logging.getLogger('NightMother')
        print("Logging setup complete")  # Debug line

    def _init_database(self):
        db_path = Path(self.config['database']['path'])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path))
        self._create_tables()
        print("Database initialized")  # Debug line

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                type TEXT,
                severity TEXT,
                description TEXT,
                source TEXT
            )
        ''')
        self.conn.commit()

    def monitor_processes(self):
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
            try:
                proc_info = proc.info
                cpu_percent = proc.cpu_percent(interval=0.1)
                if cpu_percent > 70:
                    self.log_event(
                        "High CPU Usage",
                        "WARNING",
                        f"Process {proc_info['name']} (PID: {proc_info['pid']}) CPU: {cpu_percent}%",
                        "Process Monitor"
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def log_event(self, event_type, severity, description, source):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO events (timestamp, type, severity, description, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), event_type, severity, description, source))
        self.conn.commit()
        self.logger.info(f"{severity}: {description}")

    def start(self):
        self.logger.info("NightMother Security Agent started")
        try:
            while True:
                self.monitor_processes()
                time.sleep(self.config['agent']['check_interval'])
        except KeyboardInterrupt:
            self.logger.info("Shutting down NightMother")
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
        finally:
            if hasattr(self, 'conn'):
                self.conn.close()