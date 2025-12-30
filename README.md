# BetRivals ⚽📊  
**Advanced Football Analytics Platform**

BetRivals is a web-based football analytics platform designed to provide deep, data-driven insights beyond traditional match results.  
The project integrates multiple football datasets into a **fully normalized relational database** and exposes them through **advanced analytical SQL queries** and an **interactive user interface**.

---

## 🌐 Live & Presentation Links

- **Project Website:** https://www.betrivals.com.tr  
- **Project Presentation (Canva):**  
  https://www.canva.com/design/DAG7_EE4mMo/joKvrUyNHt8dJz5ef7QshQ/edit

---

## 🎯 Project Motivation

Football performance cannot be fully explained by final scores alone.  
Metrics such as **Expected Goals (xG)**, **Shot Quality**, **Defensive Pressure (PPDA)**, and **Form Analysis** provide deeper tactical and strategic understanding.

**BetRivals** was developed to:
- Centralize football data into a unified schema
- Enable complex analytical queries
- Offer meaningful insights through filtering and aggregation
- Ensure data integrity and security

---

## 🧠 Key Objectives

- Design and implement a **3NF-normalized relational database**
- Integrate multiple football datasets (shots, matches, teams, players, seasons)
- Support **complex SQL queries** (joins, subqueries, aggregations)
- Provide advanced filtering and analytical capabilities
- Protect against **SQL Injection** via parameterized queries

---

## 🗄️ Dataset Overview

| Table Name     | Description |
|---------------|-------------|
| `players`     | Static player attributes (name, country, body type, height, weight) |
| `fut23`       | Season-dependent player attributes and FIFA-based ratings |
| `shot_data`   | Event-level shot data including xG values |
| `match_info`  | Match-level statistics and results |
| `season`      | Season-long team performance metrics |
| `teams`       | Team identifiers and league information |
| `users`       | User data with integrity constraints |

---

## 🧱 Database Design

- **Normalization:**  
  - 1NF → 2NF → **3NF**
  - Removed partial and transitive dependencies
  - Derived attributes computed dynamically (e.g. points from wins & draws)

- **ER Diagram → Relational Mapping:**  
  Carefully mapped entities and relationships to relational tables with proper primary and foreign keys.

---

## 🔍 Complex Analytical Queries

BetRivals supports advanced football analytics queries such as:

- Player shot efficiency and xG overperformance
- Team attacking and defensive context
- Opposition defensive quality analysis
- Recent form analysis using subqueries
- Match-level and season-level aggregations

These queries leverage:
- Multi-table joins
- Nested subqueries
- Conditional aggregations
- Derived metrics

---

## 🔐 Security

- **SQL Injection Protection**  
  All database interactions use **parameterized queries**, ensuring that user inputs are treated strictly as data and never executable SQL code.

---

## 🚀 Features

- Advanced filtering and autocomplete
- Interactive player, team, match, and season pages
- Complex statistical insights
- Clean, scalable relational schema
- Secure query execution

---

## 👥 Team Members

- **Osman Yahya Akıncı**
- **Talha Müderrisoğlu**
- **Bilge Bostanbaşı**
- **Abdullah Akcan**

---

## 🏫 Academic Context

This project was developed as part of:

**BLG 317E – Database Systems  
Term Project**

---

## 📌 License

This project is developed for academic and educational purposes.  
Please contact the authors for reuse or extension beyond this scope.

---

## 📣 Feedback

Questions, suggestions, or contributions are welcome.  
Feel free to explore the platform and presentation for deeper insights.