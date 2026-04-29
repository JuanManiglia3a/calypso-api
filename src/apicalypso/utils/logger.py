"""
utils/logger.py

Este módulo configura y devuelve loggers personalizados para el proyecto.
"""
import logging
import sys

class CustomFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels."""
    COLORS = {
        'DEBUG': '\033[94m',  # Azul
        'INFO': '\033[32m',   # Verde
        'WARNING': '\033[94m', # Azul
        'ERROR': '\033[91m',  # Rojo
        'CRITICAL': '\033[95m'# Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}" # Añadir color al nivel de log
        record.msg = f"{log_color}{record.getMessage()}{self.RESET}" # Añadir color al mensaje
        return super().format(record)

def configure_logger(name='perroBot_Logger', level=logging.INFO, log_to_file: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = CustomFormatter('[%(name)s] %(levelname)s:  %(message)s')
    
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        if log_to_file:
            file_handler = logging.FileHandler(log_to_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
    logger.propagate = False

    return logger
