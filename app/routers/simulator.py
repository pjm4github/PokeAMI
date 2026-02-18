"""Simulator control plane endpoints for the dashboard.

Provides status, stop, and start controls for individual simulator components.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import require_api_key

router = APIRouter(tags=["Simulator Control"])

# Map of component names to their private attribute names on SimulatorEngine
COMPONENT_MAP = {
    "meter_park": "_meter_park",
    "data_generator": "_data_generator",
    "headend": "_headend",
    "mdm": "_mdm",
    "analytics": "_analytics",
    "delivery_manager": "_delivery_manager",
}


def _get_component(simulator, name: str):
    attr = COMPONENT_MAP.get(name)
    if attr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown component: {name}. Valid: {list(COMPONENT_MAP.keys())}",
        )
    return getattr(simulator, attr)


@router.get("/simulator/status")
async def simulator_status(request: Request) -> dict:
    """Get status of all simulator components and recent events."""
    simulator = request.app.state.simulator
    components = {}
    for name, attr in COMPONENT_MAP.items():
        component = getattr(simulator, attr)
        components[name] = component.is_enabled()
    events = simulator.event_log.tail(50)
    return {"components": components, "events": events}


@router.post("/simulator/{component}/stop", dependencies=[Depends(require_api_key)])
async def stop_component(request: Request, component: str) -> dict:
    """Stop (disable) a simulator component."""
    simulator = request.app.state.simulator
    comp = _get_component(simulator, component)
    comp.stop()
    simulator.event_log.append(component, f"{component} stopped", level="warn")
    return {"component": component, "enabled": False}


@router.post("/simulator/{component}/start", dependencies=[Depends(require_api_key)])
async def start_component(request: Request, component: str) -> dict:
    """Start (enable) a simulator component."""
    simulator = request.app.state.simulator
    comp = _get_component(simulator, component)
    comp.start()
    simulator.event_log.append(component, f"{component} started")
    return {"component": component, "enabled": True}
