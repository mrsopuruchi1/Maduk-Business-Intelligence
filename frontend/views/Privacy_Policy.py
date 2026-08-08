import streamlit as st


def render_privacy_policy_page():

    # ----------------------------
    # GLOBAL STYLING (FINAL FIX)
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
        color: #111827;  /* BLACK */
    }

    /* TEXT */
    .text {
        font-size: 14.5px;
        line-height: 1.7;
        color: #111827;  /* BLACK TEXT */
    }

    /* LIST */
    .list-item {
        margin-bottom: 6px;
        color: #111827;
    }

    /* HIGHLIGHT */
    .highlight {
        color: #2563EB;  /* BLUE */
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
    <div class="hero-title">🔒 Privacy Policy</div>
    <div class="hero-subtitle">Your data privacy and security matter to us</div>
    """, unsafe_allow_html=True)

    # ----------------------------
    # INTRO
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="text">
    <b class="highlight">Maduk Business Intelligence</b> is committed to protecting
    your privacy and securing your data.<br><br>

    This policy explains how we collect, use, and safeguard your information.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 1
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">1. Information We Collect</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    We may collect:
    <br><br>

    <div class="list-item">📊 Data uploaded for analysis</div>
    <div class="list-item">📈 Usage analytics</div>
    <div class="list-item">🖱️ User interaction data</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 2
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">2. How Your Data Is Used</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    Your data helps us:
    <br><br>

    <div class="list-item">🤖 Generate insights</div>
    <div class="list-item">🧠 Improve AI models</div>
    <div class="list-item">⚙️ Enhance platform performance</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 3
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">3. Data Protection</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    We protect your data against:
    <br><br>

    • Unauthorized access<br>
    • Data loss<br>
    • Misuse
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 4
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">4. Data Sharing</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    <b class="highlight">We do NOT sell or share your data.</b><br><br>

    Your data is only used for:
    <br><br>

    • Platform functionality<br>
    • Analytics generation
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 5
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">5. User Rights</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    You can:
    <br><br>

    <div class="list-item">🗑️ Request data deletion</div>
    <div class="list-item">⛔ Stop using the platform</div>
    <div class="list-item">❓ Ask how your data is used</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # SECTION 6
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">6. Policy Updates</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    This policy may be updated periodically to reflect changes
    in the platform or legal requirements.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # CLOSE CONTAINER
    st.markdown('</div>', unsafe_allow_html=True)