import datetime

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from data.connection import db_cursor
from data.users import User


@dataclass
class Bloom:
    id: int
    sender: User
    content: str
    sent_timestamp: datetime.datetime
    rebloomed_by: Optional[str] = None
    rebloomed_at: Optional[datetime.datetime] = None
    rebloom_count: int = 0


def add_bloom(*, sender: User, content: str) -> Bloom:
    hashtags = [word[1:] for word in content.split(" ") if word.startswith("#")]

    now = datetime.datetime.now(tz=datetime.UTC)
    bloom_id = int(now.timestamp() * 1000000)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO blooms (id, sender_id, content, send_timestamp) VALUES (%(bloom_id)s, %(sender_id)s, %(content)s, %(timestamp)s)",
            dict(
                bloom_id=bloom_id,
                sender_id=sender.id,
                content=content,
                timestamp=datetime.datetime.now(datetime.UTC),
            ),
        )
        for hashtag in hashtags:
            cur.execute(
                "INSERT INTO hashtags (hashtag, bloom_id) VALUES (%(hashtag)s, %(bloom_id)s)",
                dict(hashtag=hashtag, bloom_id=bloom_id),
            )


def get_blooms_for_user(
    username: str, *, before: Optional[int] = None, limit: Optional[int] = None
) -> List[Bloom]:
    with db_cursor() as cur:
        kwargs = {"sender_username": username}
        before_clause = ""
        if before is not None:
            before_clause = "WHERE sent_timestamp < %(before_limit)s"
            kwargs["before_limit"] = before
        limit_clause = make_limit_clause(limit, kwargs)

        cur.execute(
            f"""SELECT id, sender_username, content, sent_timestamp,
              rebloomed_by, rebloomed_at, rebloom_count
            FROM (
              SELECT blooms.id, users.username AS sender_username, content,
                send_timestamp AS sent_timestamp, NULL::VARCHAR AS rebloomed_by,
                NULL::TIMESTAMP AS rebloomed_at,
                (SELECT COUNT(*) FROM reblooms WHERE bloom_id = blooms.id) AS rebloom_count
              FROM blooms INNER JOIN users ON users.id = blooms.sender_id
              WHERE users.username = %(sender_username)s
              UNION ALL
              SELECT blooms.id, author.username AS sender_username, blooms.content,
                reblooms.rebloom_timestamp AS sent_timestamp,
                rebloomer.username AS rebloomed_by,
                reblooms.rebloom_timestamp AS rebloomed_at,
                (SELECT COUNT(*) FROM reblooms AS counts WHERE counts.bloom_id = blooms.id) AS rebloom_count
              FROM reblooms
                INNER JOIN blooms ON blooms.id = reblooms.bloom_id
                INNER JOIN users AS author ON author.id = blooms.sender_id
                INNER JOIN users AS rebloomer ON rebloomer.id = reblooms.rebloomer_id
              WHERE rebloomer.username = %(sender_username)s
            ) AS user_blooms
            {before_clause}
            ORDER BY sent_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        blooms = []
        for row in cur.fetchall():
            (
                bloom_id,
                sender_username,
                content,
                timestamp,
                rebloomed_by,
                rebloomed_at,
                rebloom_count,
            ) = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                    rebloomed_by=rebloomed_by,
                    rebloomed_at=rebloomed_at,
                    rebloom_count=rebloom_count,
                )
            )
    return blooms


def add_rebloom(*, user: User, bloom_id: int) -> None:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO reblooms (rebloomer_id, bloom_id, rebloom_timestamp)
            VALUES (%(rebloomer_id)s, %(bloom_id)s, %(rebloom_timestamp)s)
            ON CONFLICT (rebloomer_id, bloom_id) DO NOTHING""",
            {
                "rebloomer_id": user.id,
                "bloom_id": bloom_id,
                "rebloom_timestamp": datetime.datetime.now(datetime.UTC),
            },
        )


def get_bloom(bloom_id: int) -> Optional[Bloom]:
    with db_cursor() as cur:
        cur.execute(
            """SELECT blooms.id, users.username, content, send_timestamp,
              (SELECT COUNT(*) FROM reblooms WHERE bloom_id = blooms.id)
            FROM blooms INNER JOIN users ON users.id = blooms.sender_id
            WHERE blooms.id = %s""",
            (bloom_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        bloom_id, sender_username, content, timestamp, rebloom_count = row
        return Bloom(
            id=bloom_id,
            sender=sender_username,
            content=content,
            sent_timestamp=timestamp,
            rebloom_count=rebloom_count,
        )


def get_blooms_with_hashtag(
    hashtag_without_leading_hash: str, *, limit: int = None
) -> List[Bloom]:
    kwargs = {
        "hashtag_without_leading_hash": hashtag_without_leading_hash,
    }
    limit_clause = make_limit_clause(limit, kwargs)
    with db_cursor() as cur:
        cur.execute(
            f"""SELECT
              blooms.id, users.username, content, send_timestamp,
              (SELECT COUNT(*) FROM reblooms WHERE bloom_id = blooms.id)
            FROM
              blooms INNER JOIN hashtags ON blooms.id = hashtags.bloom_id INNER JOIN users ON blooms.sender_id = users.id
            WHERE
              hashtag = %(hashtag_without_leading_hash)s
            ORDER BY send_timestamp DESC
            {limit_clause}
            """,
            kwargs,
        )
        rows = cur.fetchall()
        blooms = []
        for row in rows:
            bloom_id, sender_username, content, timestamp, rebloom_count = row
            blooms.append(
                Bloom(
                    id=bloom_id,
                    sender=sender_username,
                    content=content,
                    sent_timestamp=timestamp,
                    rebloom_count=rebloom_count,
                )
            )
    return blooms


def make_limit_clause(limit: Optional[int], kwargs: Dict[Any, Any]) -> str:
    if limit is not None:
        limit_clause = "LIMIT %(limit)s"
        kwargs["limit"] = limit
    else:
        limit_clause = ""
    return limit_clause
