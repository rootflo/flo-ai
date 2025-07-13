from dataclasses import dataclass
from typing import Callable, List
from functools import partial


def default_router(to_node: str) -> str:
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

    def is_default_router(self) -> bool:
        if isinstance(self.router_fn, partial):
            return self.router_fn.func.__name__ == 'default_router'
        return False
