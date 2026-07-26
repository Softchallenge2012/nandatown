#!/usr/bin/env python3
"""Print trust scores for a list of agents.

Usage:
    uv run python scripts/print_trust_scores.py
"""

from __future__ import annotations

import asyncio
import json
from typing import Iterable

from nest_core.layers.trust import Trust
from nest_core.types import AgentId, Evidence
from nest_sdk import DatasetMetadata

from nest_plugins_reference.datafacts.gift_card_recommender import GiftCardRecommenderFacts
from nest_plugins_reference.trust.score_average import ScoreAverageTrust


SELLER_COUNT = 100
BUYER_COUNT = 100
CATEGORIES = ("coffee", "gaming", "shopping", "travel", "books")


async def print_trust_scores(trust: Trust, agents: Iterable[AgentId]) -> None:
    """Print score, confidence, and sample count for each agent."""
    print("agent_id\tscore\tconfidence\tsamples")
    for agent in agents:
        rep = await trust.score(agent)
        print(f"{rep.agent_id}\t{rep.score:.3f}\t{rep.confidence:.3f}\t{rep.sample_count}")


def _seller_agent(index: int) -> AgentId:
    return AgentId(f"seller-{index:03d}")


def _buyer_agent(index: int) -> AgentId:
    return AgentId(f"buyer-{index:03d}")


def _seller_purchase_history(index: int) -> list[dict[str, object]]:
    category = CATEGORIES[index % len(CATEGORIES)]
    merchant = f"merchant-{index:03d}"
    gift_card = f"GiftCard-{index:03d}"
    amount = 25 + (index % 5) * 10
    rows: list[dict[str, object]] = []

    for offset in range(3):
        rows.append(
            {
                "record_index": f"seller-{index:03d}-record-{offset:02d}",
                "customer_id": f"customer-{index:03d}-{offset:02d}",
                "gift_card": gift_card,
                "merchant": merchant,
                "category": category,
                "amount": amount + offset * 5,
                "notes": f"{category} purchase {offset}",
            }
        )
    return rows


def _buyer_query(seller_index: int, buyer_index: int) -> str:
    category = CATEGORIES[seller_index % len(CATEGORIES)]
    merchant = f"merchant-{seller_index:03d}"
    gift_card = f"GiftCard-{seller_index:03d}"
    amount = 25 + (seller_index % 5) * 10
    is_positive = (seller_index + buyer_index) % 2 == 0
    if is_positive:
        record_index = f"seller-{seller_index:03d}-record-00"
    else:
        record_index = f"buyer-{buyer_index:03d}-mismatch-{seller_index:03d}"

    return json.dumps(
        {
            "record_index": record_index,
            "gift_card": gift_card,
            "merchant": merchant,
            "category": category,
            "amount": amount,
        }
    )


async def run_recommendation_marketplace(trust: Trust) -> tuple[list[AgentId], list[AgentId]]:
    """Simulate buyers evaluating seller recommendations and reporting trust evidence."""
    facts = GiftCardRecommenderFacts()
    sellers = [_seller_agent(index) for index in range(SELLER_COUNT)]
    buyers = [_buyer_agent(index) for index in range(BUYER_COUNT)]
    published_urls = {}

    for index, seller in enumerate(sellers):
        dataset = DatasetMetadata(
            name=f"gift-card-history-{index:03d}",
            owner=seller,
            metadata={"purchase_history_table": _seller_purchase_history(index)},
        )
        published_urls[seller] = await facts.publish(dataset)

    for buyer_index, buyer in enumerate(buyers):
        for seller_index, seller in enumerate(sellers):
            query = _buyer_query(seller_index, buyer_index)
            verdict = facts.recommend_gift_cards(published_urls[seller], query)
            await trust.report(
                seller,
                Evidence(
                    reporter=buyer,
                    subject=seller,
                    kind=verdict,
                    detail=f"recommendation query against {seller}",
                ),
            )
            await trust.report(
                buyer,
                Evidence(
                    reporter=seller,
                    subject=buyer,
                    kind=verdict,
                    detail=f"buyer evaluation for {seller}",
                ),
            )

    return sellers, buyers


async def main() -> None:
    trust = ScoreAverageTrust()
    sellers, buyers = await run_recommendation_marketplace(trust)

    print("sellers")
    await print_trust_scores(trust, sellers)
    print()
    print("buyers")
    await print_trust_scores(trust, buyers)


if __name__ == "__main__":
    asyncio.run(main())
