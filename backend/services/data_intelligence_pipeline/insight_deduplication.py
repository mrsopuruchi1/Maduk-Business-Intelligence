import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# ============================================
# 🔥 INSIGHT DEDUPLICATION ENGINE
# ============================================
def deduplicate_insights(
    ranked_insights: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Cleans and deduplicates ranked insights.

    Features:
    - Removes duplicate statements
    - Merges mirrored correlations (A→B vs B→A)
    - Keeps highest scoring version
    - Eliminates redundant insights

    Returns:
        Cleaned list of insights
    """

    try:
        if not ranked_insights:
            return []

        unique_map = {}
        final_insights = []

        # ============================================
        # 🔹 NORMALIZE KEY (CRITICAL)
        # ============================================
        def generate_key(insight: Dict[str, Any]) -> str:
            features = insight.get("features", [])
            insight_type = insight.get("type", "")

            # sort features to remove A→B vs B→A duplication
            sorted_features = sorted(features)

            return f"{insight_type}:{'-'.join(sorted_features)}"

        # ============================================
        # 🔹 DEDUPLICATE BASED ON KEY
        # ============================================
        for ins in ranked_insights:

            key = generate_key(ins)

            if key not in unique_map:
                unique_map[key] = ins
            else:
                # keep the higher score
                if ins.get("score", 0) > unique_map[key].get("score", 0):
                    unique_map[key] = ins

        # ============================================
        # 🔹 MERGE SIMILAR INSIGHTS (SOFT MATCH)
        # ============================================
        def is_similar(a: str, b: str) -> bool:
            a, b = a.lower(), b.lower()

            # simple similarity logic (fast + effective)
            return (
                a in b or b in a or
                len(set(a.split()) & set(b.split())) > 3
            )

        merged = []

        for ins in unique_map.values():

            found_similar = False

            for existing in merged:

                if is_similar(ins.get("insight", ""), existing.get("insight", "")):
                    found_similar = True

                    # keep the stronger one
                    if ins.get("score", 0) > existing.get("score", 0):
                        existing.update(ins)

                    break

            if not found_similar:
                merged.append(ins)

        # ============================================
        # 🔹 FINAL SORT
        # ============================================
        final_insights = sorted(
            merged,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        logger.info(f"Deduplicated insights: {len(ranked_insights)} → {len(final_insights)}")

        return final_insights

    except Exception as e:
        logger.exception(f"Insight deduplication failed: {str(e)}")
        return ranked_insights  # fallback (safe)