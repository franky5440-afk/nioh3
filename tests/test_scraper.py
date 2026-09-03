import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import scraper


class PickHotTest(unittest.TestCase):
    def test_recent_rss_candidates_are_resolved_when_known_pool_is_full(self):
        today = datetime.now(timezone.utc).date()
        old = (today - timedelta(days=200)).isoformat()
        recent = [(today - timedelta(days=i)).isoformat() for i in (1, 2, 3)]
        pool = [
            {"video_id": f"old-{i}", "title": f"Nioh 3 old guide {i}", "channel": "old", "url": "", "view_count": 100000 - i}
            for i in range(25)
        ]
        rss_map = {
            f"recent-{i}": {"title": f"Nioh 3 DLC guide {i}", "date": recent[i], "views": 900 - i if i else None}
            for i in range(3)
        }
        full_calls = []

        def fake_full_info(video_id):
            full_calls.append(video_id)
            if video_id in rss_map:
                return rss_map[video_id]["date"], 900
            return old, 100000

        with patch.object(scraper.time, "sleep"):
            output = scraper.pick_hot(pool, 10, rss_map, lambda title: True, fake_full_info)
        output_ids = {item["video_id"] for item in output}

        self.assertEqual(len(output), 10)
        self.assertTrue({"recent-0", "recent-1", "recent-2"} <= output_ids)
        self.assertIn("recent-0", full_calls)
        self.assertEqual(sum(item["date"] >= recent[-1] for item in output), 3)


if __name__ == "__main__":
    unittest.main()
