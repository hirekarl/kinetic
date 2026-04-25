from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any

import ladybug  # type: ignore
from google import genai

from kinetic.models.inputs import CheckInPayload

logger = logging.getLogger(__name__)

# Constants
VECTOR_DIMENSION = 768  # Standard for Gemini text-embedding-004


class LadybugClient:
    """Handles persistence of check-ins into LadybugDB (Graph + Vector)."""

    def __init__(self, db_path: str = "./kinetic.db", api_key: str | None = None) -> None:
        # Ensure path directory exists if it's not a memory db
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db = ladybug.Database(db_path)
        self.conn = ladybug.Connection(self.db)
        self._init_schema()

        # Initialize Gemini Client for embeddings
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set; embeddings will be disabled.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def _init_schema(self) -> None:
        """Create schema if it doesn't exist."""
        # Nodes
        self._safe_execute(
            f"CREATE NODE TABLE CheckIn(id UUID, timestamp TIMESTAMP, message STRING, embedding FLOAT[{VECTOR_DIMENSION}], PRIMARY KEY (id))"
        )
        self._safe_execute(
            "CREATE NODE TABLE BioMetric(id UUID, sleep_hours DOUBLE, nutrition_quality INT64, energy_level INT64, PRIMARY KEY (id))"
        )
        self._safe_execute(
            "CREATE NODE TABLE LogisticsTask(name STRING, priority STRING, PRIMARY KEY (name))"
        )
        self._safe_execute("CREATE NODE TABLE Person(name STRING, PRIMARY KEY (name))")

        # Edges
        self._safe_execute("CREATE REL TABLE HAS_BIO(FROM CheckIn TO BioMetric, ONE_ONE)")
        self._safe_execute(
            "CREATE REL TABLE MENTIONED_TASK(FROM CheckIn TO LogisticsTask, days_overdue INT64, MANY_MANY)"
        )
        self._safe_execute(
            "CREATE REL TABLE VIBE_CHECK(FROM CheckIn TO Person, score INT64, days_since INT64, MANY_MANY)"
        )

    def _safe_execute(self, query: str) -> None:
        try:
            self.conn.execute(query)
        except Exception as e:
            if "already exists" not in str(e):
                logger.debug(f"Query error (safe): {e}")

    def get_embedding(self, text: str) -> list[float]:
        """Convert text to vector embedding using Gemini API."""
        if not self.client:
            logger.error("Embedding requested but Gemini Client not initialized.")
            return [0.0] * VECTOR_DIMENSION

        try:
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return result.embeddings[0].values  # type: ignore
        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            return [0.0] * VECTOR_DIMENSION

    async def insert_checkin(self, payload: CheckInPayload, message: str) -> str:
        """Insert a parsed check-in into the graph."""
        checkin_id = str(uuid.uuid4())
        timestamp = datetime.now()
        embedding = self.get_embedding(message)

        # 1. Create CheckIn node
        self.conn.execute(
            "CREATE (c:CheckIn {id: $id, timestamp: $ts, message: $msg, embedding: $emb})",
            {"id": checkin_id, "ts": timestamp, "msg": message, "emb": embedding},
        )

        # 2. Handle Bio
        if payload.bio:
            bio_id = str(uuid.uuid4())
            self.conn.execute(
                "CREATE (b:BioMetric {id: $id, sleep_hours: $sleep, nutrition_quality: $nutr, energy_level: $eng})",
                {
                    "id": bio_id,
                    "sleep": float(payload.bio.sleep_hours or 0.0),
                    "nutr": payload.bio.nutrition_quality or 0,
                    "eng": payload.bio.energy_level or 0,
                },
            )
            self.conn.execute(
                "MATCH (c:CheckIn), (b:BioMetric) WHERE c.id = $cid AND b.id = $bid CREATE (c)-[:HAS_BIO]->(b)",
                {"cid": checkin_id, "bid": bio_id},
            )

        # 3. Handle Logistics
        if payload.logistics:
            for task in payload.logistics.tasks:
                self.conn.execute(
                    "MERGE (t:LogisticsTask {name: $name}) ON CREATE SET t.priority = $pri",
                    {"name": task.name, "pri": task.priority},
                )
                self.conn.execute(
                    "MATCH (c:CheckIn), (t:LogisticsTask) WHERE c.id = $cid AND t.name = $tname "
                    "CREATE (c)-[:MENTIONED_TASK {days_overdue: $overdue}]->(t)",
                    {"cid": checkin_id, "tname": task.name, "overdue": task.days_overdue},
                )

        # 4. Handle Relational
        if payload.relational:
            for vibe in payload.relational.vibe_checks:
                self.conn.execute("MERGE (p:Person {name: $name})", {"name": vibe.person})
                self.conn.execute(
                    "MATCH (c:CheckIn), (p:Person) WHERE c.id = $cid AND p.name = $pname "
                    "CREATE (c)-[:VIBE_CHECK {score: $score, days_since: $days}]->(p)",
                    {
                        "cid": checkin_id,
                        "pname": vibe.person,
                        "score": vibe.score,
                        "days": vibe.days_since_contact,
                    },
                )

        return checkin_id

    def get_recent_bio(self, limit: int = 7) -> list[dict[str, Any]]:
        """Fetch recent bio-metrics for trend analysis."""
        result = self.conn.execute(
            "MATCH (c:CheckIn)-[:HAS_BIO]->(b:BioMetric) "
            "RETURN b.sleep_hours, b.nutrition_quality, b.energy_level, c.timestamp "
            "ORDER BY c.timestamp DESC LIMIT $limit",
            {"limit": limit},
        )
        items = []
        while result.has_next():
            row = result.get_next()
            items.append(
                {
                    "sleep_hours": row[0],
                    "nutrition_quality": row[1],
                    "energy_level": row[2],
                    "timestamp": row[3],
                }
            )
        return items
