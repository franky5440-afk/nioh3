"""
契約：collect_videos() 該語言的頻道 RSS 一部影片都拿不到（rss_map 為空）時，
視為「YouTube 擋下雲端 IP、爬蟲失敗」，hot/new 一律回傳空 list，
交由 update_videos() 既有的「0 筆保留前一日資料」保護處理；
不可把搜尋池裡沒日期的老片當熱門遞補塞滿 10 部覆寫線上資料。

背景：09/08 雲端 run 34184534691、09/09 run 34308575319 的 RSS 全回 404/500（0 部），
pick_hot() 的「窗外遞補湊滿」把 2026-02 的老片整批寫進線上 videos_hot_zh.json，
RSS 恢復後才自癒。poe2 同日已套同樣的 fix（poe2 commit 1e6e535）。
「遞補湊滿」規則本身保留（那是冷門遊戲真的沒新片時的行為），
本測試釘死的是：RSS 0 部＝爬蟲壞掉，不是內容淡季，不得落地。

跑法：./venv/bin/python -m unittest tests.test_collect_videos_rss_blocked -v
"""
import unittest
from unittest.mock import patch

import scraper


def _video(vid, views):
    return {"video_id": vid, "title": f"仁王3 攻略 {vid}", "channel": "ch",
            "channel_id": f"UC{vid}", "view_count": views,
            "url": f"https://www.youtube.com/watch?v={vid}"}


class CollectVideosRssBlockedTest(unittest.TestCase):
    def setUp(self):
        # 搜尋池照常拿得到（flat search 沒被擋），但全都沒日期——09/08 線上的狀態
        self.pool = [_video(f"v{i}", views=100000 - i) for i in range(12)]
        for name, ret in (("yt_flat_search", self.pool), ("yt_rss_latest", []),
                          ("yt_full_info", (None, None))):
            p = patch.object(scraper, name, return_value=ret)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(scraper.time, "sleep")
        p.start()
        self.addCleanup(p.stop)

    def test_rss_zero_videos_returns_empty_hot_and_new(self):
        hot, new = scraper.collect_videos("zh")

        self.assertEqual(hot, [], "RSS 0 部＝爬蟲失敗，hot 必須回空 list 讓 update_videos 保留舊資料，"
                                  "不可拿無日期老片遞補湊滿")
        self.assertEqual(new, [], "RSS 0 部＝爬蟲失敗，new 必須回空 list")

    def test_rss_working_still_picks_normally(self):
        rss_rows = [(v["video_id"], v["title"], "2026-09-01", v["view_count"]) for v in self.pool]
        with patch.object(scraper, "yt_rss_latest", return_value=rss_rows):
            hot, new = scraper.collect_videos("zh")

        self.assertEqual(len(hot), 10, "RSS 正常時 hot 照舊產出 10 部")
        self.assertEqual(len(new), 10, "RSS 正常時 new 照舊產出 10 部")


if __name__ == "__main__":
    unittest.main()
