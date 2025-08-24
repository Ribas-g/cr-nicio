"""
Sistema de monitoramento de saúde do bot
Monitora recursos e detecta problemas antes que causem crashes
"""

import time
import threading
import psutil
import os
from loguru import logger
from typing import Optional, Callable


class HealthMonitor:
    def __init__(self, config: dict):
        self.config = config
        self.is_monitoring = False
        self.monitor_thread = None
        self.health_callbacks = []
        
        # Limites de recursos
        self.max_cpu_percent = 80.0
        self.max_memory_percent = 85.0
        self.max_disk_percent = 90.0
        
        # Contadores de saúde
        self.error_count = 0
        self.max_errors = 10
        self.last_error_time = 0
        self.error_reset_interval = 300  # 5 minutos
        
    def start_monitoring(self):
        """Inicia o monitoramento de saúde"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitor de saúde iniciado")
        
    def stop_monitoring(self):
        """Para o monitoramento de saúde"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Monitor de saúde parado")
        
    def add_health_callback(self, callback: Callable):
        """Adiciona callback para notificações de saúde"""
        self.health_callbacks.append(callback)
        
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.is_monitoring:
            try:
                self._check_system_health()
                self._check_error_rate()
                time.sleep(5)  # Verificar a cada 5 segundos
            except Exception as e:
                logger.error(f"Erro no monitor de saúde: {e}")
                time.sleep(10)
                
    def _check_system_health(self):
        """Verifica saúde do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.max_cpu_percent:
                logger.warning(f"CPU alta: {cpu_percent}%")
                self._notify_health_issue("high_cpu", cpu_percent)
                
            # Memória
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_percent:
                logger.warning(f"Memória alta: {memory.percent}%")
                self._notify_health_issue("high_memory", memory.percent)
                
            # Disco
            disk = psutil.disk_usage('/')
            if disk.percent > self.max_disk_percent:
                logger.warning(f"Disco alto: {disk.percent}%")
                self._notify_health_issue("high_disk", disk.percent)
                
        except Exception as e:
            logger.error(f"Erro ao verificar saúde do sistema: {e}")
            
    def _check_error_rate(self):
        """Verifica taxa de erros"""
        current_time = time.time()
        
        # Reset contador se passou muito tempo
        if current_time - self.last_error_time > self.error_reset_interval:
            self.error_count = 0
            
        # Se muitos erros em pouco tempo, notificar
        if self.error_count > self.max_errors:
            logger.warning(f"Muitos erros detectados: {self.error_count}")
            self._notify_health_issue("high_error_rate", self.error_count)
            self.error_count = 0  # Reset após notificação
            
    def record_error(self):
        """Registra um erro para monitoramento"""
        self.error_count += 1
        self.last_error_time = time.time()
        
    def _notify_health_issue(self, issue_type: str, value: float):
        """Notifica problemas de saúde"""
        for callback in self.health_callbacks:
            try:
                callback(issue_type, value)
            except Exception as e:
                logger.error(f"Erro no callback de saúde: {e}")
                
    def get_health_status(self) -> dict:
        """Retorna status atual de saúde"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "error_count": self.error_count,
                "is_monitoring": self.is_monitoring
            }
        except Exception as e:
            logger.error(f"Erro ao obter status de saúde: {e}")
            return {"error": str(e)}
