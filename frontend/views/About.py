import streamlit as st


def render_about_page():

    # ----------------------------
    # GLOBAL STYLING (FINAL)
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
    <div class="hero-title">📊 About Maduk Business Intelligence</div>
    <div class="hero-subtitle">Your AI Business Consultant</div>
    """, unsafe_allow_html=True)

    # ----------------------------
    # ABOUT
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="text">
    <b class="highlight">Maduk Business Intelligence</b> is an AI-powered SaaS platform
    built for digital agencies and service businesses.<br><br>

    It helps you <b>analyze marketing, sales, and customer data</b> to:
    <br><br>

    • Understand performance<br>
    • Identify growth opportunities<br>
    • Make smarter business decisions<br><br>

    Powered by <b>data science and machine learning</b>, the platform delivers:
    <br><br>

    • Actionable insights<br>
    • Predictive analytics<br>
    • Intelligent forecast & recommendations
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # FEATURES
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What the Platform Does</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    <div class="list-item">📊 Analyze campaign performance</div>
    <div class="list-item">🤖 AI-powered predictions</div>
    <div class="list-item">⚠️ Churn detection</div>
    <div class="list-item">📈 Revenue forecasting</div>
    <div class="list-item">🚀 Channel optimization</div>
    <div class="list-item">💡 Smart insights</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # TARGET USERS
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Who It’s For</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    <div class="list-item">🏢 Digital agencies</div>
    <div class="list-item">📊 Consultants</div>
    <div class="list-item">💻 SaaS businesses</div>
    <div class="list-item">🧑‍💼 Freelancers</div>
    <div class="list-item">📈 Growth-focused teams</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # MISSION
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Our Mission</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    Our mission is to make <b class="highlight">advanced data intelligence simple and accessible</b>.<br><br>

    Helping businesses:
    <br><br>

    • Make smarter decisions<br>
    • Improve revenue & performance<br>
    • Scale confidently
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # DEVELOPER
    # ----------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Developer</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="text">
    Maduk Business Intelligence was built by <b class="highlight">Sopuruchi Maduka</b>,
    a Data Scientist & Machine Learning Specialist. He is also a graduate of Electrical & Electronic Engineering.<br><br>

    With a background in data science, machine learning, and engineering, Mr. Maduka combined:
    <br><br>

    • Artificial Intelligence<br>
    • Predictive Data Analytics<br>
    • Machine Learning<br>
    • Business Intelligence<br><br>

    to build this AI software that turns data into <b>real insights that help businesses grow</b>.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # CLOSE CONTAINER
    st.markdown('</div>', unsafe_allow_html=True)