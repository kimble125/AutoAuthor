import asyncio
import pandas as pd
import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from autoauthor.pipeline import AutoAuthorPipeline, PipelineResult

async def fix_missing_plans():
    print("🚀 누락된 7개 영화 기획안 + 연계 시너지 기획안 생성 시작...")
    
    csv_path = "results/키워드분석_통합_수동분석_20260329_202848.csv"
    if not os.path.exists(csv_path):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    # Group by title
    titles = df["콘텐츠명(주제)"].unique().tolist()
    
    pipeline = AutoAuthorPipeline()
    result = PipelineResult(mode="manual_recovery")
    
    analyses_by_title = {}
    for title in titles:
        # Convert df rows back to list of dicts for the generator
        title_df = df[df["콘텐츠명(주제)"] == title]
        analyses = []
        for _, row in title_df.iterrows():
            analyses.append({
                "keyword": row["하위_키워드"],
                "google_trend_pct": row["구글_트렌드(%)"],
                "total_demand": row["통합검색수요(전체)"],
                "naver_docs": row["총문서량(네이버)"],
                "naver_stars": row["추천도(네이버)"],
                "kakao_docs": row["총문서량(다음)"],
                "kakao_stars": row["추천도(티스토리)"],
                "yt_total_videos": row["총영상수(유튜브)"],
                "yt_stars": row["추천도(유튜브)"],
                "is_golden": row["추천도(네이버)"] == "★★★" or row["추천도(티스토리)"] == "★★★"
            })
        analyses_by_title[title] = analyses
        
        print(f"  📝 '{title}' 기획안 생성 중...")
        plans = await pipeline.generator.generate_multi_platform(
            title=title,
            content_type="movie",
            keywords=analyses,
            platforms=["tistory"]
        )
        result.plans.extend(plans)

    # Synergy Plan
    print(f"\n🔗 [Synergy] {len(titles)}개 작품 연계 기획안 생성 중...")
    synergy_plans = await pipeline.generator.generate_synergy_plan(
        titles=titles,
        category="movie",
        analyses_by_title=analyses_by_title,
        platforms=["tistory"]
    )
    result.plans.extend(synergy_plans)

    # Export to files
    if result.plans:
        saved_files = pipeline._export_plans(result.plans, "복구")
        print(f"\n✅ 완료! 총 {len(saved_files)}개의 파일이 생성되었습니다.")

if __name__ == "__main__":
    asyncio.run(fix_missing_plans())
