
"""Population simulation tools for OpenPK-Twin."""

from .population import simulate_virtual_population_iv_bolus

from .two_compartment import (
    simulate_virtual_population_two_compartment_iv_bolus,
)

__all__ = [
    "simulate_virtual_population_iv_bolus",
    "simulate_virtual_population_two_compartment_iv_bolus",
]
