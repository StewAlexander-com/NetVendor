"""
Runtime Logger for NetVendor

This module provides structured logging of runtime behavior for troubleshooting
and performance analysis. Logs are written to a file in the output directory.

Usage:
    Enable logging via environment variable:
        NETVENDOR_LOG=1 python3 NetVendor.py input_file.txt
    
    Or enable programmatically:
        from netvendor.utils.runtime_logger import RuntimeLogger
        logger = RuntimeLogger(enabled=True)
        logger.log_event("processing_start", {"file": "input.txt"})
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class RuntimeLogger:
    """
    Structured logger for NetVendor runtime behavior.
    
    Logs are written in JSONL format (one JSON object per line) for easy parsing
    and analysis. Each log entry includes:
    - timestamp: UTC ISO-8601 timestamp
    - event_type: Type of event (e.g., "processing_start", "mac_found", "error")
    - event_data: Event-specific data
    - context: Additional context (file being processed, etc.)
    """
    
    def __init__(self, enabled: bool | None = None, log_file: str | Path | None = None):
        """
        Initialize the runtime logger.
        
        Args:
            enabled: If True, enable logging. If None, check NETVENDOR_LOG env var.
            log_file: Path to log file. If None, defaults to output/netvendor_runtime.log
        """
        # Check if logging is enabled
        if enabled is None:
            enabled = os.getenv("NETVENDOR_LOG", "0") in ("1", "true", "True", "yes", "Yes")
        
        self.enabled = enabled
        self.log_file: Optional[Path] = None
        self.log_entries: list[Dict[str, Any]] = []
        
        if self.enabled:
            # Set up log file path
            if log_file is None:
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                self.log_file = output_dir / "netvendor_runtime.log"
            else:
                self.log_file = Path(log_file)
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write initialization entry
            self.log_event("logger_init", {
                "log_file": str(self.log_file),
                "enabled": True
            })
    
    def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any] | None = None,
        context: Dict[str, Any] | None = None
    ) -> None:
        """
        Log a runtime event.
        
        Args:
            event_type: Type of event (e.g., "processing_start", "mac_found", "error")
            event_data: Event-specific data dictionary
            context: Additional context dictionary
        """
        if not self.enabled:
            return
        
        entry = {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "event_type": event_type,
            "event_data": event_data or {},
            "context": context or {}
        }
        
        self.log_entries.append(entry)
        
        # Write immediately to file (for troubleshooting crashes)
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            # Silently fail if logging fails (don't break main functionality)
            pass
    
    def log_processing_start(self, input_file: str, flags: Dict[str, Any] | None = None) -> None:
        """Log the start of file processing."""
        self.log_event("processing_start", {
            "input_file": str(input_file),
            "file_size": os.path.getsize(input_file) if os.path.exists(input_file) else 0
        }, context=flags or {})
    
    def log_processing_end(self, stats: Dict[str, Any]) -> None:
        """Log the end of file processing with statistics."""
        self.log_event("processing_end", stats)
    
    def log_file_type_detection(self, file_type: str, detection_method: str) -> None:
        """Log file type detection."""
        self.log_event("file_type_detection", {
            "detected_type": file_type,
            "detection_method": detection_method
        })
    
    def log_mac_processing(self, mac: str, vendor: str | None = None, vlan: str | None = None, port: str | None = None) -> None:
        """Log MAC address processing."""
        self.log_event("mac_processed", {
            "mac": mac,
            "vendor": vendor,
            "vlan": vlan,
            "port": port
        })
    
    def log_error(self, error_type: str, error_message: str, error_details: Dict[str, Any] | None = None) -> None:
        """Log an error event."""
        self.log_event("error", {
            "error_type": error_type,
            "error_message": error_message,
            **{**(error_details or {})}
        })
    
    def log_api_call(self, service: str, mac: str, success: bool, response_time_ms: float | None = None) -> None:
        """Log an API vendor lookup call."""
        self.log_event("api_call", {
            "service": service,
            "mac": mac,
            "success": success,
            "response_time_ms": response_time_ms
        })
    
    def log_output_generation(self, output_type: str, output_file: str, record_count: int | None = None) -> None:
        """Log output file generation."""
        self.log_event("output_generated", {
            "output_type": output_type,
            "output_file": str(output_file),
            "record_count": record_count
        })
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "seconds") -> None:
        """Log a performance metric."""
        self.log_event("performance_metric", {
            "metric_name": metric_name,
            "value": value,
            "unit": unit
        })
    
    def log_cache_operation(self, operation: str, cache_type: str, details: Dict[str, Any] | None = None) -> None:
        """Log cache operations (load, save, hit, miss)."""
        self.log_event("cache_operation", {
            "operation": operation,  # "load", "save", "hit", "miss"
            "cache_type": cache_type,  # "oui_cache", "failed_lookups"
            **(details or {})
        })
    
    def flush(self) -> None:
        """Flush any buffered log entries (currently writes immediately, but kept for API compatibility)."""
        # Logs are written immediately, but this method exists for future buffering
        pass
    
    def close(self) -> None:
        """Close the logger and write final entry."""
        if self.enabled:
            self.log_event("logger_close", {
                "total_entries": len(self.log_entries)
            })


# Global logger instance (lazy initialization)
_global_logger: Optional[RuntimeLogger] = None


def get_logger(enabled: bool | None = None) -> RuntimeLogger:
    """
    Get or create the global runtime logger instance.
    
    Args:
        enabled: If provided, override the default enabled state.
    
    Returns:
        RuntimeLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = RuntimeLogger(enabled=enabled)
    
    return _global_logger


def reset_logger() -> None:
    """Reset the global logger (useful for testing)."""
    global _global_logger
    _global_logger = None

