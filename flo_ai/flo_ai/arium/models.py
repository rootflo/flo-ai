from dataclasses import dataclass, field
from typing import Callable, Dict, List
from functools import partial
from flo_ai.arium.memory import BaseMemory


def default_router(
    to_node: str,
    memory: BaseMemory,
    navigation_thresholds: Dict[str, int] = {},
) -> str:
    nt = navigation_thresholds.get(to_node, None)
    if nt and nt <= 0:
        raise ValueError(f'Navigation threshold for {to_node} hit, in default router')
    return to_node


@dataclass
class StartNode:
    name = '__start__'


@dataclass
class EndNode:
    name = '__end__'


@dataclass
class Edge:
    router_fn: Callable | partial
    to_nodes: List[str]
    navigation_threshold: Dict[str, int] = field(default_factory=dict)

    def is_default_router(self) -> bool:
        if isinstance(self.router_fn, partial):
            return self.router_fn.func.__name__ == 'default_router'
        return False
