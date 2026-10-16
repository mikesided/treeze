"""
Name:         network_simulator.py
Description:  Class that exposes simulated network delay

"""
# ______________________________________________________________________________________________________________________
# Imports
from __future__ import annotations
import asyncio

import random

from dataclasses import dataclass

# ______________________________________________________________________________________________________________________


@dataclass(frozen=True)
class NetworkSimulator:
    rtt: float = 50  # ms
    jitter: float = 10  # ms
    packet_loss: float = 0.01  # probability

    async def delay_round_trip(self):
        await self.delay_one_way()
        await self.delay_one_way()

    async def delay_one_way(self):
        delay = self.rtt / 2
        delay += random.uniform(-self.jitter, self.jitter)

        while random.random() < min(0.99, self.packet_loss):
            delay += self.rtt

        await asyncio.sleep(max(0.0, delay) / 1000)
        