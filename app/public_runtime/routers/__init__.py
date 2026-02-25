from .agent_routes import router as agent_router
from .discovery_routes import router as discovery_router
from .follow_routes import router as follow_router
from .forum_routes import router as forum_router
from .health_routes import router as health_router
from .protocol_routes import router as protocol_router
from .sim_routes import router as sim_router

__all__ = [
    "agent_router",
    "discovery_router",
    "follow_router",
    "forum_router",
    "health_router",
    "protocol_router",
    "sim_router",
]
