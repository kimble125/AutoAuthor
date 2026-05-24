import types
import unittest

from autoauthor.config import AutoAuthorConfig
from autoauthor.pipeline import AutoAuthorPipeline
from autoauthor.sources.google_trends import GoogleTrendsSource


async def _zero_trend(self, keyword):
    return 0


GoogleTrendsSource.get_keyword_recency_score = _zero_trend


def _ad_metric(pipeline, value, status="ok", keyword="테스트"):
    metric = pipeline._metric(value, status)
    if status == "ok":
        metric.update({"match_type": "exact", "matched_keyword": keyword})
    return metric


class KeywordScoringTests(unittest.IsolatedAsyncioTestCase):
    def _pipeline(self):
        return AutoAuthorPipeline(AutoAuthorConfig(request_delay=0, youtube_api_key=""))

    async def test_failed_measurements_are_not_golden(self):
        pipeline = self._pipeline()

        async def market(self, keyword):
            return self._metric(0, "error", "forced failure")

        async def naver_blog(self, keyword):
            return self._metric(-1, "error", "forced failure")

        async def kakao_blog(self, keyword):
            return self._metric(-1, "error", "forced failure")

        pipeline._measure_naver_ad_metrics = types.MethodType(market, pipeline)
        pipeline._measure_naver_blog_metrics = types.MethodType(naver_blog, pipeline)
        pipeline._measure_kakao_blog_metrics = types.MethodType(kakao_blog, pipeline)

        rows = await pipeline._analyze_keywords(["실패 케이스"], "테스트")

        self.assertFalse(rows[0]["is_golden"])
        self.assertEqual(rows[0]["demand_status"], "no_demand")
        self.assertEqual(rows[0]["naver_stars"], "-")
        self.assertIn("키워드 직접수요 없음/미확인", rows[0]["golden_reason"])

    async def test_youtube_missing_key_does_not_promote_saturated_keyword(self):
        pipeline = self._pipeline()

        async def market(self, keyword):
            return _ad_metric(self, 10000, keyword=keyword)

        async def naver_blog(self, keyword):
            return self._metric(999999, "ok")

        async def kakao_blog(self, keyword):
            return self._metric(999999, "ok")

        pipeline._measure_naver_ad_metrics = types.MethodType(market, pipeline)
        pipeline._measure_naver_blog_metrics = types.MethodType(naver_blog, pipeline)
        pipeline._measure_kakao_blog_metrics = types.MethodType(kakao_blog, pipeline)

        rows = await pipeline._analyze_keywords(["경쟁 많은 키워드"], "테스트")

        self.assertFalse(rows[0]["is_golden"])
        self.assertEqual(rows[0]["yt_status"], "missing_key")
        self.assertEqual(rows[0]["yt_stars"], "-")

    async def test_valid_low_saturation_keyword_is_golden(self):
        pipeline = self._pipeline()

        async def market(self, keyword):
            return _ad_metric(self, 100000, keyword=keyword)

        async def naver_blog(self, keyword):
            return self._metric(100, "ok")

        async def kakao_blog(self, keyword):
            return self._metric(50000, "ok")

        pipeline._measure_naver_ad_metrics = types.MethodType(market, pipeline)
        pipeline._measure_naver_blog_metrics = types.MethodType(naver_blog, pipeline)
        pipeline._measure_kakao_blog_metrics = types.MethodType(kakao_blog, pipeline)

        rows = await pipeline._analyze_keywords(["테스트 황금 키워드"], "테스트")

        self.assertTrue(rows[0]["is_golden"])
        self.assertEqual(rows[0]["naver_stars"], "★★★")
        self.assertGreaterEqual(rows[0]["score"], 80)
        self.assertIn("네이버 직접수요 대비 문서량 낮음", rows[0]["golden_reason"])

    async def test_related_ad_keyword_match_is_not_golden(self):
        pipeline = self._pipeline()

        async def market(self, keyword):
            if keyword == "테스트":
                return _ad_metric(self, 100000, keyword=keyword)
            metric = self._metric(50000, "ok")
            metric.update({"match_type": "related", "matched_keyword": "테스트 관련"})
            return metric

        async def naver_blog(self, keyword):
            return self._metric(10, "ok")

        async def kakao_blog(self, keyword):
            return self._metric(10, "ok")

        pipeline._measure_naver_ad_metrics = types.MethodType(market, pipeline)
        pipeline._measure_naver_blog_metrics = types.MethodType(naver_blog, pipeline)
        pipeline._measure_kakao_blog_metrics = types.MethodType(kakao_blog, pipeline)

        rows = await pipeline._analyze_keywords(["테스트 애매한 키워드"], "테스트")

        self.assertFalse(rows[0]["is_golden"])
        self.assertEqual(rows[0]["keyword_demand_status"], "related_only")
        self.assertIn("직접수요", rows[0]["golden_reason"])

    async def test_tiny_direct_demand_is_not_golden(self):
        pipeline = self._pipeline()

        async def market(self, keyword):
            return _ad_metric(self, 10, keyword=keyword)

        async def naver_blog(self, keyword):
            return self._metric(0, "ok")

        async def kakao_blog(self, keyword):
            return self._metric(0, "ok")

        pipeline._measure_naver_ad_metrics = types.MethodType(market, pipeline)
        pipeline._measure_naver_blog_metrics = types.MethodType(naver_blog, pipeline)
        pipeline._measure_kakao_blog_metrics = types.MethodType(kakao_blog, pipeline)

        rows = await pipeline._analyze_keywords(["테스트 초저수요"], "테스트")

        self.assertFalse(rows[0]["is_golden"])
        self.assertEqual(rows[0]["verdict"], "보류: 직접수요 기준 미달")
        self.assertLessEqual(rows[0]["score"], 45)
        self.assertIn("100회 미만", rows[0]["golden_reason"])

    async def test_metadata_only_keyword_is_not_golden(self):
        pipeline = self._pipeline()

        async def market(self, keyword):
            return _ad_metric(self, 100000, keyword=keyword)

        async def naver_blog(self, keyword):
            return self._metric(0, "ok")

        async def kakao_blog(self, keyword):
            return self._metric(0, "ok")

        pipeline._measure_naver_ad_metrics = types.MethodType(market, pipeline)
        pipeline._measure_naver_blog_metrics = types.MethodType(naver_blog, pipeline)
        pipeline._measure_kakao_blog_metrics = types.MethodType(kakao_blog, pipeline)

        rows = await pipeline._analyze_keywords(["Susan Lacy 감독 영화"], "스필버그")

        self.assertFalse(rows[0]["is_golden"])
        self.assertLess(rows[0]["relevance_score"], 50)
        self.assertIn("관련도 낮음", rows[0]["golden_reason"])


if __name__ == "__main__":
    unittest.main()
