import webview
import os
import re
from datetime import datetime

# 1. PYTHON BACKEND 
class Api:
    def __init__(self):
        # Default path: User's Documents folder
        docs_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        if not os.path.exists(docs_dir):
            docs_dir = os.path.expanduser('~')
            
        self.current_filepath = os.path.join(docs_dir, "GATE_DA_Syllabus_Tracker.md")

    def init_db(self, data):
        parent_dir = os.path.dirname(self.current_filepath)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
            except Exception as e:
                print(f"Could not create path: {e}")

        if not os.path.exists(self.current_filepath):
            self._write_initial_md(data)

        return {
            "state": self.parse_md(),
            "filepath": self.current_filepath
        }

    def _write_initial_md(self, data):
        try:
            with open(self.current_filepath, 'w', encoding='utf-8') as f:
                f.write("# 📟 GATE DA (Data Science & AI) Tracker\n\n")
                f.write("> Auto-generated Syllabus Tracker\n\n")
                for module in data:
                    f.write(f"## {module['title']}\n")
                    for topic in module['topics']:
                        f.write(f"- [ ] {topic}\n")
                    f.write("\n")
        except Exception as e:
            print(f"Error writing file: {e}")

    def parse_md(self):
        state = {}
        if not os.path.exists(self.current_filepath):
            return state

        with open(self.current_filepath, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(r'- \[(x| )\] (.*?)(?: \(Completed: (.*?)\))?$', line.strip())
                if match:
                    is_completed = match.group(1).lower() == 'x'
                    topic = match.group(2).strip()
                    date = match.group(3) if match.group(3) else ""
                    state[topic] = {"completed": is_completed, "date": date}
        return state

    def toggle_task(self, topic, completed):
        if not os.path.exists(self.current_filepath):
            return self.parse_md()

        lines = []
        with open(self.current_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")

        with open(self.current_filepath, 'w', encoding='utf-8') as f:
            for line in lines:
                match = re.match(r'- \[(x| )\] (.*?)(?: \(Completed: (.*?)\))?$', line.strip())
                if match and match.group(2).strip() == topic:
                    if completed:
                        f.write(f"- [x] {topic} (Completed: {now_str})\n")
                    else:
                        f.write(f"- [ ] {topic}\n")
                else:
                    f.write(line)

        return self.parse_md()

    def load_dropped_file(self, filepath):
        if filepath and os.path.exists(filepath) and filepath.endswith('.md'):
            self.current_filepath = filepath
            return {"success": True, "filepath": self.current_filepath, "state": self.parse_md()}
        return {"success": False, "error": "Please drop a valid Markdown (.md) file."}



# 2. HTML/CSS/JS FRONTEND

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GATE DA Tracker</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Special+Elite&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-paper: #f4ecd8;
      --ink: #2b2b2b;
      --ink-light: #525252;
      --highlight: #d1bfae;
      --border: 2px solid var(--ink);
      --shadow: 4px 4px 0px var(--ink);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-paper);
      color: var(--ink);
      font-family: 'Special Elite', monospace;
      line-height: 1.6;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E");
    }

    /* Navbar / Header Controls */
    .top-nav {
      padding: 15px 20px 0;
      display: flex;
      justify-content: flex-start;
      align-items: center;
    }
    
    .burger-btn {
      background: #e8dec8;
      border: var(--border);
      padding: 8px 14px;
      cursor: pointer;
      font-family: inherit;
      font-weight: bold;
      font-size: 1rem;
      box-shadow: 2px 2px 0px var(--ink);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .burger-btn:active {
      transform: translate(1px, 1px);
      box-shadow: 1px 1px 0px var(--ink);
    }

    /* Drag & Drop Overlay */
    #dropOverlay {
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(244, 236, 216, 0.95);
      border: 4px dashed var(--ink);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease;
    }
    #dropOverlay.active {
      opacity: 1;
      pointer-events: auto;
    }
    .drop-message { font-size: 1.8rem; font-weight: bold; text-align: center; }

    header {
      text-align: center;
      padding: 10px 20px 20px;
      border-bottom: var(--border);
      margin-bottom: 25px;
    }
    header h1 {
      font-size: 2.2rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      text-decoration: underline;
      text-decoration-thickness: 2px;
      margin-bottom: 5px;
    }
    header p { color: var(--ink-light); font-size: 1rem; }

    .container { max-width: 900px; margin: 0 auto; padding: 0 20px; flex: 1; width: 100%; }

    /* Countdown Widget */
    .countdown-box {
      border: var(--border);
      box-shadow: var(--shadow);
      background: #2b2b2b;
      color: #f4ecd8;
      padding: 15px;
      margin-bottom: 25px;
      text-align: center;
    }
    .countdown-box h4 {
      font-size: 0.95rem;
      letter-spacing: 1px;
      margin-bottom: 5px;
      color: var(--highlight);
      text-transform: uppercase;
    }
    .timer-display {
      font-size: 1.5rem;
      font-weight: bold;
      letter-spacing: 2px;
    }

    /* Infographic Progress Bar */
    .infographic-box {
      border: var(--border);
      box-shadow: var(--shadow);
      background: #faf4e6;
      padding: 20px;
      margin-bottom: 40px;
      text-align: center;
    }
    .infographic-box h3 {
      font-size: 1.2rem;
      margin-bottom: 15px;
      border-bottom: 1px dashed var(--ink);
      display: inline-block;
    }
    .ascii-bar-container {
      font-size: 1.5rem;
      letter-spacing: 2px;
      font-weight: bold;
      margin-bottom: 10px;
      white-space: nowrap;
      overflow: hidden;
    }
    .stats-text { font-size: 1rem; color: var(--ink-light); }

    /* Flowchart / Roadmap Steps */
    .flowchart { position: relative; }
    .flowchart::before {
      content: ''; position: absolute; top: 30px; bottom: 30px; left: 30px;
      width: 4px; background: var(--ink); z-index: 1;
    }

    .flow-step { position: relative; margin-bottom: 30px; padding-left: 70px; z-index: 2; }

    .step-node {
      position: absolute; left: 12px; top: 16px;
      width: 40px; height: 40px; border-radius: 50%;
      background: var(--bg-paper); border: var(--border);
      display: flex; align-items: center; justify-content: center;
      font-weight: bold; font-size: 1.1rem; box-shadow: 2px 2px 0px var(--ink); z-index: 3;
    }

    .flow-card {
      background: #faf4e6;
      padding: 20px;
      border: var(--border);
      box-shadow: var(--shadow);
      cursor: pointer;
      transition: transform 0.1s, box-shadow 0.1s;
    }
    .flow-card:active {
      transform: translate(2px, 2px);
      box-shadow: 2px 2px 0px var(--ink);
    }

    .card-header {
      display: flex; justify-content: space-between; align-items: flex-start;
      margin-bottom: 10px; border-bottom: 1px dashed var(--ink); padding-bottom: 8px;
    }
    .card-title { font-size: 1.2rem; font-weight: bold; }
    
    .badge {
      border: 1px solid var(--ink); padding: 4px 8px;
      font-size: 0.8rem; background: var(--highlight);
      font-weight: bold; color: var(--ink);
    }
    .card-footer { margin-top: 15px; font-size: 0.9rem; font-weight: bold; }

    /* Footer */
    footer {
      text-align: center;
      padding: 16px;
      border-top: var(--border);
      margin-top: 40px;
      background: #e8dec8;
      font-size: 1rem;
      font-weight: bold;
      letter-spacing: 1px;
      box-shadow: 0px -2px 0px var(--ink);
    }

    /* Common Overlay Styles */
    .overlay {
      position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(0, 0, 0, 0.6); opacity: 0; pointer-events: none;
      transition: opacity 0.2s; z-index: 100;
    }
    .overlay.active { opacity: 1; pointer-events: auto; }

    /* Topic Drawer Styles */
    .drawer {
      position: fixed; top: 0; right: 0; width: 500px; max-width: 90vw; height: 100vh;
      background: var(--bg-paper); border-left: var(--border);
      box-shadow: -5px 0 15px rgba(0,0,0,0.5); z-index: 101;
      transform: translateX(100%); transition: transform 0.3s;
      display: flex; flex-direction: column;
    }
    .drawer.active { transform: translateX(0); }

    .drawer-header {
      padding: 24px; border-bottom: var(--border); background: #faf4e6;
      display: flex; justify-content: space-between; align-items: flex-start;
    }
    .drawer-title { font-size: 1.4rem; font-weight: bold; text-decoration: underline; }
    
    .drawer-close {
      background: var(--highlight); border: var(--border);
      width: 36px; height: 36px; cursor: pointer; font-family: inherit;
      font-size: 1.2rem; font-weight: bold; box-shadow: 2px 2px 0px var(--ink);
    }
    .drawer-close:active { transform: translate(1px, 1px); box-shadow: 1px 1px 0px var(--ink); }

    .drawer-content { padding: 24px; overflow-y: auto; flex: 1; }

    .topic-list { list-style: none; }
    .topic-item {
      display: flex; flex-direction: column;
      padding: 12px; border: var(--border); margin-bottom: 12px;
      background: #faf4e6; box-shadow: 2px 2px 0px var(--ink);
    }
    
    .topic-row { display: flex; align-items: flex-start; gap: 12px; }
    
    input[type="checkbox"] {
      appearance: none; width: 20px; height: 20px; border: 2px solid var(--ink);
      background: #fff; cursor: pointer; position: relative; flex-shrink: 0; margin-top: 2px;
    }
    input[type="checkbox"]:checked::after {
      content: 'X'; position: absolute; top: -4px; left: 3px;
      font-size: 1.2rem; font-weight: bold; color: var(--ink); font-family: 'Special Elite';
    }
    
    .topic-label { font-size: 1rem; cursor: pointer; font-weight: bold; }
    .topic-date { font-size: 0.8rem; color: var(--ink-light); margin-left: 32px; font-style: italic; }
    .completed-text { text-decoration: line-through; opacity: 0.7; }

    /* Side Info Drawer (Burger Menu) */
    .info-sidebar {
      position: fixed; top: 0; left: 0; width: 420px; max-width: 85vw; height: 100vh;
      background: #faf4e6; border-right: var(--border);
      box-shadow: 5px 0 15px rgba(0,0,0,0.5); z-index: 102;
      transform: translateX(-100%); transition: transform 0.3s ease;
      display: flex; flex-direction: column;
    }
    .info-sidebar.active { transform: translateX(0); }

    .info-header {
      padding: 20px; border-bottom: var(--border); background: #e8dec8;
      display: flex; justify-content: space-between; align-items: center;
    }
    .info-header h2 { font-size: 1.3rem; text-decoration: underline; }

    .info-content { padding: 20px; overflow-y: auto; flex: 1; }
    
    .info-card {
      border: var(--border);
      background: var(--bg-paper);
      padding: 15px;
      margin-bottom: 15px;
      box-shadow: 2px 2px 0px var(--ink);
    }
    .info-card h4 {
      font-size: 0.95rem;
      border-bottom: 1px dashed var(--ink);
      padding-bottom: 5px;
      margin-bottom: 8px;
    }
    .info-card p {
      font-size: 0.9rem;
      color: var(--ink);
      font-weight: bold;
    }
  </style>
</head>
<body>

  <!-- Drag & Drop Overlay Zone -->
  <div id="dropOverlay">
    <div class="drop-message">📥 Drop Markdown (.md) File Here</div>
  </div>

  <!-- Top Navbar Controls -->
  <div class="top-nav">
    <button class="burger-btn" onclick="toggleInfoSidebar()">
      <span>☰</span> EXAM INFO
    </button>
  </div>

  <header>
    <h1>GATE DA Tracker</h1>
    <p>Markdown-Backed Native Roadmap Tracker</p>
  </header>

  <div class="container">
    <!-- GATE DA 2027 Countdown Widget -->
    <div class="countdown-box">
      <h4>⏳ Countdown to GATE DA 2027 (Feb 5, 2027) ⏳</h4>
      <div class="timer-display" id="timerDisplay">Calculating time...</div>
    </div>

    <!-- Infographic Progress Bar -->
    <div class="infographic-box">
      <h3>-- DATA SCIENCE PROGRESS --</h3>
      <div class="ascii-bar-container" id="asciiBar">[....................] 0%</div>
      <div class="stats-text" id="statsText">Fetching data...</div>
    </div>

    <div class="flowchart" id="flowchart"></div>
  </div>

  <!-- Made with love by Ujjwal Sharma -->
  <footer>
    Made with ❤️ by Ujjwal Sharma
  </footer>

  <!-- Sidebar Overlay -->
  <div class="overlay" id="overlay"></div>

  <!-- Burger Menu Info Sidebar -->
  <div class="info-sidebar" id="infoSidebar">
    <div class="info-header">
      <h2>📌 GATE 2027 Schedule</h2>
      <button class="drawer-close" onclick="toggleInfoSidebar()">X</button>
    </div>
    <div class="info-content">
      <div class="info-card">
        <h4>🚀 Online Registration Starts</h4>
        <p>August 14, 2026</p>
        <p style="font-weight: normal; font-size: 0.8rem; color: var(--ink-light);">(via the GATE 2027 Portal)</p>
      </div>

      <div class="info-card">
        <h4>📅 Regular Closing Date (No Late Fee)</h4>
        <p>September 21, 2026</p>
      </div>

      <div class="info-card">
        <h4>⚠️ Extended Closing Date (With Late Fee)</h4>
        <p>September 30, 2026</p>
      </div>

      <div class="info-card" style="background: #e8dec8;">
        <h4>🎯 GATE DA Exam Date</h4>
        <p>February 5, 2027</p>
      </div>

      <div class="info-card">
        <h4>🏆 Result Declaration</h4>
        <p>March 19, 2027</p>
      </div>
    </div>
  </div>

  <!-- Topic Drawer -->
  <div class="drawer" id="drawer">
    <div class="drawer-header">
      <div>
        <h2 class="drawer-title" id="drawerTitle">Module Title</h2>
        <div style="margin-top:10px;" id="drawerBadges"></div>
      </div>
      <button class="drawer-close" id="drawerClose">X</button>
    </div>
    <div class="drawer-content">
      <ul class="topic-list" id="topicList"></ul>
    </div>
  </div>

  <script>
    const roadmapData = [
      {
        id: 1, title: "1A. Engineering Mathematics - Linear Algebra", marks: "~10 Marks",
        topics: ["Vector space & Subspaces", "Matrix Multiplication & Properties", "Systems of Linear Equations ($Ax = b$)", "Projection Matrix", "Types of Matrices (Symmetric, Hermitian, Orthogonal)", "Determinant & Trace Properties", "Orthogonal Matrix & Gram-Schmidt Process", "Eigenvalue and Eigenvector", "Symmetric Matrix & Spectral Theorem", "Projection Matrix (Review with Eigenvalues)", "Similarity of Matrix", "Diagonalisation & Polynomial Matrix", "$A^T A$ and $A A^T$ properties", "Singular Value Decomposition (SVD)", "Rank Nullity Theorem", "4 Fundamental Subspaces (Nullspace, Column space, Row space, Left Nullspace)", "Orthogonal Decomposition", "Quadratic Form Optimisation", "Partition Matrix"]
      },
      {
        id: 2, title: "1B. Engineering Mathematics - Probability & Statistics", marks: "~15 Marks",
        topics: ["Counting Techniques & Combinatorics", "Basics of Probability Theory & Axioms", "Independent & Disjoint Events", "Conditional Probability & Bayes Theorem", "Conditional Expectation & Variance", "Discrete Distributions (Bernoulli, Binomial, Poisson, Geometric)", "Joint & Marginal PMF, CDF", "Continuous Distributions (Uniform, Exponential, Normal, Gaussian)", "Joint & Marginal PDF", "Covariance [X, Y] / Correlation coefficient", "Descriptive Statistics (Mean, Median, Mode, Variance, Standard Deviation)", "Chi-square ($\\chi^2$) and t-distribution", "Inferential Statistics (Hypothesis Testing, Confidence Intervals, MLE, z-test, t-test)"]
      },
      {
        id: 3, title: "1C. Engineering Mathematics - Calculus & Optimisation", marks: "~10 Marks",
        topics: ["Basics of Functions & Single Variable Calculus", "Limits & Continuity", "Differentiation & Partial Derivatives", "1st Derivative Test", "2nd Derivative Test (Maxima & Minima)", "Multivariate Calculus & Gradients", "Optimization Techniques (Gradient Descent, Convex Functions, Taylor Series)"]
      },
      {
        id: 4, title: "2. Artificial Intelligence", marks: "~10 Marks",
        topics: ["Propositional Logic (Syntax, Semantics, Validity)", "Predicate Logic (First-Order Logic, Quantifiers)", "Uniform Search Strategies (BFS, DFS, Uniform Cost Search)", "Informed Search Strategies (A* Search, Heuristics, Greedy Best-First)", "Adversarial Search (Minimax Algorithm, Alpha-Beta Pruning)", "Bayesian Networks (Conditional Independence, Exact & Approximate Inference)"]
      },
      {
        id: 5, title: "3. Practice & Revision Block 1", marks: "Revision Phase",
        topics: ["Practice Linear Algebra Questions & PYQs (3 Days)", "Practice Probability & Statistics Questions & PYQs (3 Days)", "Practice Calculus & Optimisation Problems (3 Days)", "Review mistakes and clear conceptual gaps using GateXAiml & DSAI GATE"]
      },
      {
        id: 6, title: "4. General Aptitude", marks: "~15 Marks",
        topics: ["Verbal Ability (English Grammar, Sentence Completion, Vocabulary)", "Reading Comprehension & Critical Reasoning", "Quantitative Aptitude (Data Interpretation, Charts, Tables, Graphs)", "Numerical Computation (Ratios, Percentages, Permutations, Probability)", "Analytical Reasoning & Deductive Logic", "Spatial Aptitude (Transformation, Paper Folding, Patterns, Assemblies)"]
      },
      {
        id: 7, title: "5. Machine Learning", marks: "~15 Marks",
        topics: ["Simple Linear Regression (Linear algebra view & Probabilistic view)", "Multiple Linear Regression", "Ridge Regression & Regularization ($L1/L2$)", "Overfitting / Underfitting (Bias-Variance Tradeoff)", "Logistic Regression", "Naive Bayes Classifier", "Linear Discriminant Analysis (LDA - Bayesian & Fisher)", "K-Nearest Neighbors (KNN)", "Decision Trees (Information Gain, Gini Impurity, Pruning)", "Support Vector Machine (SVM - Hard, Soft Margin, Kernel Trick Basics)", "Neural Networks (Perceptron, Multi-Layer Perceptron, Backpropagation)", "Clustering (K-Means, Hierarchical Clustering)", "Principal Component Analysis (PCA - Variance & Basis View)"]
      },
      {
        id: 8, title: "6. Database Management Systems (DBMS)", marks: "~13 Marks",
        topics: ["Keys (Candidate, Primary, Super, Foreign Keys)", "SQL Queries (DDL, DML, Nested Queries, Joins, Group By)", "Relational Algebra (RA) Operators & Tuple Calculus", "Entity-Relationship (ER) Model & ER-to-Relational Mapping", "Normalisation (1NF, 2NF, 3NF, BCNF & Functional Dependencies)", "File Organisation & Indexing (B-Trees, B+ Trees)", "Data Warehousing (Star Schema, Snowflake Schema, OLAP vs OLTP)"]
      },
      {
        id: 9, title: "7. Practice & Revision Block 2", marks: "Revision Phase",
        topics: ["Practice AI Search Algorithms & Bayesian Nets (2 Days)", "Review Engineering Mathematics (Linear Algebra, Probability, Calculus) (5 Days)", "Solve GATE DA mock tests on GateXAiml & DSAI GATE"]
      },
      {
        id: 10, title: "8. Data Structures, Algorithms & Python", marks: "~14 Marks",
        topics: ["Python Programming Basics (Variables, Control Flow, Functions)", "Python Data Structures (Lists, Tuples, Sets, Dictionaries)", "Data Analysis Libraries (NumPy Arrays, Pandas DataFrames)", "Asymptotic Notation & Time/Space Complexity Analysis", "Basic Data Structures (Arrays, Linked Lists, Stacks, Queues)", "Trees & Binary Search Trees (BST Operations, Traversals)", "Heaps & Priority Queues", "Searching & Sorting Algorithms (Bubble, Merge, Quick, Binary Search)", "Graph Algorithms (BFS, DFS, Shortest Path - Dijkstra)"]
      },
      {
        id: 11, title: "9. Final Practice & PYQ Phase", marks: "Final Prep",
        topics: ["Practice Linear Algebra PYQs & Selected Mock Questions (2 Days)", "Practice Probability & Statistics PYQs (2 Days)", "Practice Calculus & Optimisation PYQs (2 Days)", "Practice DBMS PYQs & SQL Queries (2 Days)", "Practice AI Logic & Search PYQs (2 Days)", "Practice Data Structures & Algorithms PYQs in Python (2 Days)", "Full Length Mock Test Execution on https://gatexaiml.in/"]
      }
    ];

    let savedState = {};
    let currentOpenId = null;

    // Load initial data from Python Backend
    window.addEventListener('pywebviewready', async function() {
      const initData = await window.pywebview.api.init_db(roadmapData);
      savedState = initData.state;
      renderFlowchart();
      updateInfographic();
    });

    /* Countdown Timer Logic (GATE DA 2027: Feb 5, 2027) */
    const targetExamDate = new Date("February 5, 2027 00:00:00").getTime();

    function updateCountdown() {
      const now = new Date().getTime();
      const difference = targetExamDate - now;

      if (difference <= 0) {
        document.getElementById('timerDisplay').innerText = "🎉 EXAM DAY HAS ARRIVED!";
        return;
      }

      const days = Math.floor(difference / (1000 * 60 * 60 * 24));
      const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((difference % (1000 * 60)) / 1000);

      document.getElementById('timerDisplay').innerText = 
        `${days}d : ${String(hours).padStart(2, '0')}h : ${String(minutes).padStart(2, '0')}m : ${String(seconds).padStart(2, '0')}s`;
    }

    setInterval(updateCountdown, 1000);
    updateCountdown();

    /* Burger Menu Info Sidebar Toggles */
    function toggleInfoSidebar() {
      const infoSidebar = document.getElementById('infoSidebar');
      const overlay = document.getElementById('overlay');
      const isActive = infoSidebar.classList.contains('active');

      if (isActive) {
        infoSidebar.classList.remove('active');
        overlay.classList.remove('active');
      } else {
        infoSidebar.classList.add('active');
        overlay.classList.add('active');
      }
    }

    /* Drag & Drop File Handling */
    window.addEventListener('dragover', (e) => {
      e.preventDefault();
      document.getElementById('dropOverlay').classList.add('active');
    });

    document.getElementById('dropOverlay').addEventListener('dragleave', (e) => {
      e.preventDefault();
      document.getElementById('dropOverlay').classList.remove('active');
    });

    document.getElementById('dropOverlay').addEventListener('drop', async (e) => {
      e.preventDefault();
      document.getElementById('dropOverlay').classList.remove('active');
      
      if (e.dataTransfer.files.length > 0) {
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile.path) {
          const res = await window.pywebview.api.load_dropped_file(droppedFile.path);
          if (res.success) {
            savedState = res.state;
            renderFlowchart();
            updateInfographic();
            if(currentOpenId) {
              const data = roadmapData.find(item => item.id === currentOpenId);
              renderDrawerTopics(data);
            }
          } else {
            alert(res.error || "Could not load file.");
          }
        }
      }
    });

    function updateInfographic() {
      let total = 0;
      let completed = 0;
      
      roadmapData.forEach(mod => {
        mod.topics.forEach(t => {
          total++;
          if (savedState[t] && savedState[t].completed) completed++;
        });
      });

      const percentage = total === 0 ? 0 : Math.round((completed / total) * 100);
      
      const barLength = 20;
      const filledBlocks = Math.round((percentage / 100) * barLength);
      const emptyBlocks = barLength - filledBlocks;
      const bar = `[${'#'.repeat(filledBlocks)}${'.'.repeat(emptyBlocks)}]`;
      
      document.getElementById('asciiBar').innerText = `${bar} ${percentage}%`;
      document.getElementById('statsText').innerText = `TOPICS MASTERED: ${completed} / ${total}`;
    }

    function renderFlowchart() {
      const flowchartContainer = document.getElementById('flowchart');
      flowchartContainer.innerHTML = '';
      
      roadmapData.forEach((item, idx) => {
        let modCompleted = 0;
        item.topics.forEach(t => { if(savedState[t] && savedState[t].completed) modCompleted++; });
        
        const isDone = modCompleted === item.topics.length;
        const statusText = isDone ? '[COMPLETED]' : `[${modCompleted}/${item.topics.length}]`;

        const stepEl = document.createElement('div');
        stepEl.className = 'flow-step';
        stepEl.innerHTML = `
          <div class="step-node">${idx + 1}</div>
          <div class="flow-card" onclick="openDrawer(${item.id})">
            <div class="card-header">
              <div class="card-title" style="${isDone ? 'text-decoration: line-through;' : ''}">${item.title}</div>
              <span class="badge">${item.marks}</span>
            </div>
            <div class="card-footer">> STATUS: ${statusText} ... click to expand _</div>
          </div>
        `;
        flowchartContainer.appendChild(stepEl);
      });
    }

    function openDrawer(id) {
      currentOpenId = id;
      const data = roadmapData.find(item => item.id === id);
      
      document.getElementById('drawerTitle').innerText = data.title;
      document.getElementById('drawerBadges').innerHTML = `<span class="badge">${data.marks}</span>`;
      
      renderDrawerTopics(data);

      document.getElementById('drawer').classList.add('active');
      document.getElementById('overlay').classList.add('active');
    }

    function renderDrawerTopics(data) {
      const topicList = document.getElementById('topicList');
      topicList.innerHTML = '';
      
      data.topics.forEach((topic, index) => {
        const isCompleted = savedState[topic] && savedState[topic].completed;
        const dateStr = (savedState[topic] && savedState[topic].date) ? `Date Logged: ${savedState[topic].date}` : '';
        
        const li = document.createElement('li');
        li.className = 'topic-item';
        
        const checkboxId = `chk_${data.id}_${index}`;
        
        li.innerHTML = `
          <div class="topic-row">
            <input type="checkbox" id="${checkboxId}" ${isCompleted ? 'checked' : ''} onchange="handleCheck('${topic}', this)" />
            <label class="topic-label ${isCompleted ? 'completed-text' : ''}" for="${checkboxId}">${topic}</label>
          </div>
          ${dateStr ? `<div class="topic-date">> ${dateStr}</div>` : ''}
        `;
        topicList.appendChild(li);
      });
    }

    async function handleCheck(topic, checkbox) {
      const completed = checkbox.checked;
      
      const label = checkbox.nextElementSibling;
      if(completed) label.classList.add('completed-text');
      else label.classList.remove('completed-text');

      if (window.pywebview) {
        savedState = await window.pywebview.api.toggle_task(topic, completed);
        updateInfographic();
        renderFlowchart();
        if(currentOpenId) {
          const data = roadmapData.find(item => item.id === currentOpenId);
          renderDrawerTopics(data);
        }
      }
    }

    function closeAllDrawers() {
      document.getElementById('drawer').classList.remove('active');
      document.getElementById('infoSidebar').classList.remove('active');
      document.getElementById('overlay').classList.remove('active');
      currentOpenId = null;
    }

    document.getElementById('drawerClose').addEventListener('click', closeAllDrawers);
    document.getElementById('overlay').addEventListener('click', closeAllDrawers);
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAllDrawers(); });
  </script>
</body>
</html>
"""


# 3. APP INITIALIZATION

if __name__ == '__main__':
    api = Api()
    webview.create_window(
        'GATE DA Tracker', 
        html=HTML_CONTENT, 
        js_api=api, 
        width=1050, 
        height=850, 
        background_color='#f4ecd8'
    )
    webview.start()