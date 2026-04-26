from __future__ import annotations

import asyncio
import json
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
        self._lock = asyncio.Lock()  # Serialize access to the single connection
        self._init_schema_sync()

        # Initialize Gemini Client for embeddings
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set; embeddings will be disabled.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def _init_schema_sync(self) -> None:
        """Create schema synchronously during init."""
        # Nodes
        self._safe_execute_sync(
            f"CREATE NODE TABLE CheckIn(id UUID, timestamp TIMESTAMP, message STRING, embedding FLOAT[{VECTOR_DIMENSION}], PRIMARY KEY (id))"
        )
        self._safe_execute_sync(
            "CREATE NODE TABLE BioMetric(id UUID, sleep_hours DOUBLE, nutrition_quality INT64, energy_level INT64, PRIMARY KEY (id))"
        )
        self._safe_execute_sync(
            "CREATE NODE TABLE LogisticsTask(name STRING, priority STRING, subtasks STRING, completed_subtasks STRING, status STRING, PRIMARY KEY (name))"
        )
        self._safe_execute_sync("CREATE NODE TABLE Person(name STRING, PRIMARY KEY (name))")

        # Edges
        self._safe_execute_sync("CREATE REL TABLE HAS_BIO(FROM CheckIn TO BioMetric, ONE_ONE)")
        self._safe_execute_sync(
            "CREATE REL TABLE MENTIONED_TASK(FROM CheckIn TO LogisticsTask, days_overdue INT64, MANY_MANY)"
        )
        self._safe_execute_sync(
            "CREATE REL TABLE VIBE_CHECK(FROM CheckIn TO Person, score INT64, days_since INT64, MANY_MANY)"
        )

    def _safe_execute_sync(self, query: str) -> None:
        try:
            self.conn.execute(query)
        except Exception as e:
            if "already exists" not in str(e):
                logger.debug(f"Query error (safe): {e}")

    async def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:  # noqa: ANN401
        """Execute a query with serialized access."""
        async with self._lock:
            return self.conn.execute(query, parameters or {})

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
        await self.execute(
            f"CREATE (c:CheckIn {{id: CAST($id, 'UUID'), timestamp: $ts, message: $msg, embedding: CAST($emb, 'FLOAT[{VECTOR_DIMENSION}]')}})",
            {"id": checkin_id, "ts": timestamp, "msg": message, "emb": embedding},
        )

        # 2. Handle Bio
        if payload.bio:
            bio_id = str(uuid.uuid4())
            await self.execute(
                "CREATE (b:BioMetric {id: CAST($id, 'UUID'), sleep_hours: $sleep, nutrition_quality: $nutr, energy_level: $eng})",
                {
                    "id": bio_id,
                    "sleep": float(payload.bio.sleep_hours or 0.0),
                    "nutr": payload.bio.nutrition_quality or 0,
                    "eng": payload.bio.energy_level or 0,
                },
            )
            await self.execute(
                "MATCH (c:CheckIn), (b:BioMetric) WHERE c.id = CAST($cid, 'UUID') AND b.id = CAST($bid, 'UUID') CREATE (c)-[:HAS_BIO]->(b)",
                {"cid": checkin_id, "bid": bio_id},
            )

        # 3. Handle Logistics
        if payload.logistics:
            for task in payload.logistics.tasks:
                subtasks_json = json.dumps(task.subtasks)
                completed_json = json.dumps(task.completed_subtasks)

                # MERGE the task node (keeping properties updated)
                await self.execute(
                    "MERGE (t:LogisticsTask {name: $name}) "
                    "ON CREATE SET t.priority = $pri, t.subtasks = $sub, t.completed_subtasks = $comp, t.status = $stat "
                    "ON MATCH SET t.priority = $pri, t.subtasks = $sub, t.completed_subtasks = $comp, t.status = $stat",
                    {
                        "name": task.name,
                        "pri": task.priority,
                        "sub": subtasks_json,
                        "comp": completed_json,
                        "stat": task.status,
                    },
                )
                await self.execute(
                    "MATCH (c:CheckIn), (t:LogisticsTask) WHERE c.id = CAST($cid, 'UUID') AND t.name = $tname "
                    "CREATE (c)-[:MENTIONED_TASK {days_overdue: $overdue}]->(t)",
                    {"cid": checkin_id, "tname": task.name, "overdue": task.days_overdue},
                )

        # 4. Handle Relational
        if payload.relational:
            for vibe in payload.relational.vibe_checks:
                await self.execute("MERGE (p:Person {name: $name})", {"name": vibe.person})
                await self.execute(
                    "MATCH (c:CheckIn), (p:Person) WHERE c.id = CAST($cid, 'UUID') AND p.name = $pname "
                    "CREATE (c)-[:VIBE_CHECK {score: $score, days_since: $days}]->(p)",
                    {
                        "cid": checkin_id,
                        "pname": vibe.person,
                        "score": vibe.score,
                        "days": vibe.days_since_contact,
                    },
                )

        return checkin_id

    async def get_latest_bio(self) -> dict[str, Any] | None:
        """Fetch the most recent bio-metric record."""
        result = await self.execute(
            "MATCH (c:CheckIn)-[:HAS_BIO]->(b:BioMetric) "
            "RETURN b.sleep_hours, b.nutrition_quality, b.energy_level "
            "ORDER BY c.timestamp DESC LIMIT 1"
        )
        if result.has_next():
            row = result.get_next()
            return {
                "sleep_hours": row[0],
                "nutrition_quality": row[1],
                "energy_level": row[2],
            }
        return None

    async def get_all_tasks(self) -> list[dict[str, Any]]:
        """Fetch all unique tasks mentioned across all check-ins."""
        result = await self.execute(
            "MATCH (c:CheckIn)-[r:MENTIONED_TASK]->(t:LogisticsTask) "
            "RETURN t.name, t.priority, r.days_overdue, t.subtasks, t.completed_subtasks, t.status, c.timestamp "
            "ORDER BY c.timestamp DESC"
        )
        tasks = {}
        while result.has_next():
            row = result.get_next()
            name = row[0]
            if name not in tasks:
                tasks[name] = {
                    "name": name,
                    "priority": row[1],
                    "days_overdue": row[2],
                    "subtasks": json.loads(row[3] or "[]"),
                    "completed_subtasks": json.loads(row[4] or "[]"),
                    "status": row[5] or "pending",
                }
        return list(tasks.values())

    async def get_all_vibes(self) -> list[dict[str, Any]]:
        """Fetch the latest vibe check for every known person."""
        result = await self.execute(
            "MATCH (c:CheckIn)-[r:VIBE_CHECK]->(p:Person) "
            "RETURN p.name, r.score, r.days_since, c.timestamp "
            "ORDER BY c.timestamp DESC"
        )
        vibes = {}
        while result.has_next():
            row = result.get_next()
            name = row[0]
            if name not in vibes:
                vibes[name] = {
                    "person": name,
                    "score": row[1],
                    "days_since_contact": row[2],
                }
        return list(vibes.values())

    async def get_recent_bio(self, limit: int = 7) -> list[dict[str, Any]]:
        """Fetch recent bio-metrics for trend analysis."""
        result = await self.execute(
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

    async def clear_database(self) -> None:
        """Wipe all nodes and edges from the graph."""
        try:
            await self.execute("MATCH (n) DETACH DELETE n")
            logger.info("Database wiped successfully.")
        except Exception as e:
            logger.error(f"Error wiping database: {e}")
