#!/usr/bin/env python3
"""One-off script: 清空数据库所有帖子/话题，保留用户。需传入 DATABASE_URL 或使用环境变量。"""

import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import create_engine, text


def main():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("Usage: DATABASE_URL='postgresql://...' python scripts/clear_topics_posts.py", file=sys.stderr)
        sys.exit(1)
    # 可选：为 PostgreSQL 加上 sslmode（阿里云 RDS 常需）
    parsed = urlparse(url)
    if parsed.scheme and "postgresql" in parsed.scheme:
        query = parse_qs(parsed.query)
        if "sslmode" not in query:
            query["sslmode"] = ["prefer"]
            parsed = parsed._replace(query=urlencode(query, doseq=True))
        url = urlunparse(parsed)
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        updated_items = 0
        try:
            r1 = conn.execute(text("UPDATE favorite_category_items SET topic_id = NULL WHERE topic_id IS NOT NULL"))
            conn.commit()
            updated_items = r1.rowcount
        except Exception as e:
            conn.rollback()
            print(f"跳过 favorite_category_items 更新: {e}", file=sys.stderr)
        # 2. 删除所有 topics（级联删除 posts 及所有关联表）
        r2 = conn.execute(text("DELETE FROM topics"))
        conn.commit()
        deleted_topics = r2.rowcount
    print(f"已清空: 更新 favorite_category_items {updated_items} 行, 删除 topics {deleted_topics} 条（帖子及关联数据已级联删除）。用户表未动。")


if __name__ == "__main__":
    main()
