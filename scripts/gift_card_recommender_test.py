# SPDX-License-Identifier: Apache-2.0
"""Tests for gift-card recommendation DataFacts plugin."""

from __future__ import annotations

import asyncio
import json

from nest_sdk import AgentId, DatasetMetadata

from nest_plugins_reference.datafacts.gift_card_recommender import GiftCardRecommenderFacts


async def main():

    facts = GiftCardRecommenderFacts()
    dataset = DatasetMetadata(
        name="gift-card-history",
        owner=AgentId("merchant-ops"),
        metadata={
            "purchase_history_table": [
                {
                    "record_index": "r-001",
                    "customer_id": "c-001",
                    "gift_card": "Starbucks",
                    "merchant": "Starbucks",
                    "category": "coffee",
                    "amount": 25,
                    "notes": "birthday coworker",
                },
                {
                    "record_index": "r-002",
                    "customer_id": "c-002",
                    "gift_card": "Amazon",
                    "merchant": "Amazon",
                    "category": "shopping",
                    "amount": 50,
                    "notes": "birthday teen",
                },
                {
                    "record_index": "r-003",
                    "customer_id": "c-003",
                    "gift_card": "Starbucks",
                    "merchant": "Starbucks",
                    "category": "coffee",
                    "amount": 20,
                    "notes": "thank you teacher",
                },
            ]
        },
    )

    url = await facts.publish(dataset)
    fetched = await facts.fetch(url)
    print(fetched.name)# "gift-card-history"

    coffee_rows = facts.search_purchase_history(
        url,
        json.dumps(
            {
                "record_index": "r-001",
                "gift_card": "",
                "merchant": "",
                "category": "coffee",
                "amount": "",
            }
        ),
    )
    print(len(coffee_rows)) # 2
    print([row["gift_card"] for row in coffee_rows])


# PYTHONPATH=packages/nest-core:packages/nest-sdk:packages/nest-plugins-reference python gift_card_recommender_test.py
if __name__ == "__main__":
    asyncio.run(main())

