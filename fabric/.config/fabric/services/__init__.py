# Fabric Services
# Centralized service layer for the Fabric bar

from .animator import Animator, AnimationGroup, animate_property
from .config import Config, get_config, load_config, save_config
from .monitor_manager import MonitorManager, Monitor, get_monitor_manager
from .metrics import MetricsProvider, get_metrics_provider, NetworkStats, DiskStats, BatteryStats
from .workspace_manager import WorkspaceManagerService
from .mpris import MprisPlayer, MprisPlayerManager

__all__ = [
    # Animator
    "Animator",
    "AnimationGroup",
    "animate_property",
    # Config
    "Config",
    "get_config",
    "load_config",
    "save_config",
    # Monitor Manager
    "MonitorManager",
    "Monitor",
    "get_monitor_manager",
    # Metrics
    "MetricsProvider",
    "get_metrics_provider",
    "NetworkStats",
    "DiskStats",
    "BatteryStats",
    # Workspace Manager
    "WorkspaceManagerService",
    # MPRIS
    "MprisPlayer",
    "MprisPlayerManager",
]
