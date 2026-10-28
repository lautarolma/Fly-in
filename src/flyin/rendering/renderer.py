"""Colored terminal rendering (visual feedback, REQ-VIS-1).

Writes to a stream that is never stdout, so the official per-turn lines stay byte-for-byte clean.
"""

from __future__ import annotations

import sys
from typing import TextIO

from flyin.domain.graph import Graph


class Renderer:
    """Renders zones and drones with ANSI colors on a separate stream."""

    def __init__(self, graph: Graph, stream: TextIO | None = None) -> None:
        self.graph = graph
        self.stream = stream if stream is not None else sys.stderr

    def render(self, turn: int) -> None:
        """Render the current simulation state to the visual stream."""
        raise NotImplementedError
