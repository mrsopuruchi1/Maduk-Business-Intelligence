import time
from typing import Generator, Dict, Any

# =========================
# SHARED MODULES
# =========================
from backend.services.shared.data_upload import load_data
from backend.services.shared.data_cleaning import clean_data
from backend.services.shared.report_generation import generate_pdf_report

# =========================
# PIPELINE MODULES
# =========================
from .data_analysis import analyze_data
from .insight_ranking import rank_insights
from .insight_deduplication import deduplicate_insights
from .business_context_detection import detect_business_context
from .chart_generation import generate_focused_charts
from .ai_reasoning import generate_ai_reasoning
from .executive_summary import generate_executive_summary
from .recommendation_engine import generate_recommendations



# =========================================================
# 🚀 STREAMING DECISION INTELLIGENCE PIPELINE (11 STEPS)
# =========================================================
def run_pipeline_stream(file) -> Generator[Dict[str, Any], None, None]:

    start_total = time.perf_counter()

    def step_output(message, progress):
        return {
            "log": str(message),
            "progress": int(progress)
        }

    # =========================
    # SAFE DEFAULTS
    # =========================
    df = None
    analysis = {}
    ranked_insights = []
    clean_insights = []
    context = {}
    charts = {}
    reasoning = {}
    summary = ""
    recommendations = []
    pdf_report = ""

    # =========================================================
    # 🔹 STEP 1: LOAD DATA
    # =========================================================
    try:
        yield step_output("🟡 [1/11] Loading data...", 5)

        loaded = load_data(file)

        df = loaded[0] if isinstance(loaded, tuple) else loaded

        if df is None or getattr(df, "empty", False):
            raise ValueError("Loaded dataset is empty")

        yield step_output("⚪ Data loaded", 10)

    except Exception as e:
        yield {
            "log": f"❌ Step 1 failed: {str(e)}",
            "progress": 100,
            "done": True,
            "data": {}
        }
        return

    # =========================================================
    # 🔹 STEP 2: CLEAN DATA
    # =========================================================
    try:
        yield step_output("🟡 [2/11] Cleaning data...", 15)

        df = clean_data(df)

        if df is None or getattr(df, "empty", False):
            raise ValueError("Dataset empty after cleaning")

        yield step_output("⚪ Data cleaned", 20)

    except Exception as e:
        yield {
            "log": f"❌ Step 2 failed: {str(e)}",
            "progress": 100,
            "done": True,
            "data": {}
        }
        return

    # =========================================================
    # 🔹 STEP 3: ANALYZE DATA
    # =========================================================
    try:
        yield step_output("🟡 [3/11] Analyzing data...", 30)

        analysis = analyze_data(df)

        yield step_output("⚪ Analysis complete", 40)

    except Exception as e:
        yield {
            "log": f"❌ Step 3 failed: {str(e)}",
            "progress": 100,
            "done": True,
            "data": {}
        }
        return

    # =========================================================
    # 🔹 STEP 4–10: INSIGHTS + INTELLIGENCE
    # =========================================================
    try:
        yield step_output("🟡 [4/11] Ranking insights...", 45)
        ranked_insights = rank_insights(analysis)
        yield step_output("⚪ Insights ranked", 50)

        yield step_output("🟡 [5/11] Cleaning insights...", 55)
        clean_insights = deduplicate_insights(ranked_insights)
        yield step_output("⚪ Insights refined", 60)

        yield step_output("🟡 [6/11] Detecting business context...", 65)
        context = detect_business_context(analysis)
        yield step_output("⚪ Context identified", 70)

        yield step_output("🟡 [7/11] Generating charts...", 75)
        charts = generate_focused_charts(df, analysis, context)
        yield step_output("⚪ Charts ready", 80)

        yield step_output("🟡 [8/11] Generating AI reasoning...", 85)
        reasoning = generate_ai_reasoning(analysis, clean_insights, context)
        yield step_output("⚪ Reasoning complete", 88)

        yield step_output("🟡 [9/11] Creating executive summary...", 90)
        summary = generate_executive_summary(analysis, context, reasoning)
        yield step_output("⚪ Summary ready", 92)

        yield step_output("🟡 [10/11] Generating recommendations...", 95)
        recommendations = generate_recommendations(analysis, reasoning, context)
        yield step_output("⚪ Recommendations ready", 97)

    except Exception as e:
        yield {
            "log": f"❌ Pipeline failed: {str(e)}",
            "progress": 100,
            "done": True,
            "data": {}
        }
        return

    # =========================================================
    # 🔹 STEP 11: BUILD REPORT + FINAL OUTPUT
    # =========================================================
    try:
        yield step_output("🟡 [11/11] Building report...", 98)

        # =========================
        # METRICS (UI READY)
        # =========================
        metrics = {
            "rows": df.shape[0],
            "columns": df.shape[1],
        }

        try:
            metrics["missing_values"] = int(df.isnull().sum().sum())
        except Exception:
            metrics["missing_values"] = 0

        # =========================
        # FINAL UI RESPONSE MODEL
        # =========================
        final_output = {
            "summary": summary,
            "insights": clean_insights,
            "recommendations": recommendations,
            "charts": charts,
            "metrics": metrics,
        }

        # =========================
        # PDF REPORT GENERATION
        # =========================
        pdf_report = generate_pdf_report(
            df,
            analysis,
            charts,
            {
                "summary": summary,
                "insights": clean_insights,
                "recommendations": recommendations,
                "reasoning": reasoning.get("reasoning", ""),
                "risks": reasoning.get("risks", []),
                "opportunities": reasoning.get("opportunities", []),
            }
        )

        yield step_output("⚪ Report ready", 99)

    except Exception as e:
        yield {
            "log": f"❌ Step 11 failed: {str(e)}",
            "progress": 100,
            "done": True,
            "data": {}
        }
        return

    # =========================================================
    # 🚀 FINAL STREAM OUTPUT (SINGLE SOURCE OF TRUTH)
    # =========================================================
    total_time = time.perf_counter() - start_total

    yield {
        "log": f"✅ Pipeline completed in {total_time:.2f}s",
        "progress": 100,
        "done": True,
        "data": {
            **final_output,
            "pdf_report": pdf_report
        }
    }