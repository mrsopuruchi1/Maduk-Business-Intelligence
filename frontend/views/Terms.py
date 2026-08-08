import streamlit as st


def render_terms_page():

    # ----------------------------
    # GLOBAL STYLING (CONSISTENT DESIGN SYSTEM)
    # ----------------------------
    st.markdown("""
    <style>
    .main-container {
        max-width: 1000px;
        margin: auto;
        padding-top: 20px;
    }

    /* HERO */
    .hero-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 5px;
        color: #111827;
    }

    .hero-subtitle {
        color: #374151;
        font-size: 15px;
        margin-bottom: 25px;
    }

    /* CARD */
    .card {
        background-color: #0F172A;  /* DARK BLUE */
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
    }

    /* SECTION */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 8px;
        color: #111827;
    }

    /* TEXT */
    .text {
        font-size: 14.5px;
        line-height: 1.7;
        color: #111827;
    }

    /* LIST */
    .list-item {
        margin-bottom: 6px;
        color: #111827;
    }

    /* HIGHLIGHT */
    .highlight {
        color: #2563EB;
        font-weight: 600;
    }

    </style>
    """, unsafe_allow_html=True)

    # ----------------------------
    # MAIN CONTAINER
    # ----------------------------
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # ----------------------------
    # HERO
    # ----------------------------
    st.markdown("""
    <div class="hero-title">📜 Terms & Conditions</div>
    <div class="hero-subtitle">
    Please read these terms carefully before using the platform
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------
    # INTRO
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="text">
    Welcome to <b class="highlight">Maduk Business Intelligence</b>.<br><br>

    By accessing or using this platform, you agree to comply with
    these terms and conditions.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 1
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">1. Use of the Platform</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    The platform provides <b>AI-powered analytics</b> for businesses.<br><br>

    It supports decision-making through:
    <br><br>

    • Data analysis<br>
    • Predictive intelligence<br>
    • Performance insights
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 2
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">2. User Responsibilities</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    Users must:
    <br><br>

    <div class="list-item">✔ Ensure data accuracy</div>
    <div class="list-item">✔ Have permission to use data</div>
    <div class="list-item">✔ Use the platform legally</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 3
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">3. No Guaranteed Outcomes</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    While we use <b>advanced machine learning</b>, results are
    <b>not guaranteed</b>.<br><br>

    Insights should guide decisions, not replace judgment.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 4
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">4. Data Usage</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    Your data is used for:
    <br><br>

    • Analytics<br>
    • Predictions<br>
    • Insights<br><br>

    We do <b>not own your data</b>.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 5
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">5. Platform Changes</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    Features and policies may change to improve the platform.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 6
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">6. Acceptance</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    Continued use of the platform means you accept these terms.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # CLOSE CONTAINER
    st.markdown('</div>', unsafe_allow_html=True)