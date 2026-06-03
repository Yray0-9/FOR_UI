# Objectives of the Study

The primary objective of this study is to develop **SafeBooks: A Web-Based Bookkeeping Platform for Client Transaction Entry Records with Financial Analytics and Rule-Based Predictive Forecasting** that centralizes client financial record management, supports compliance monitoring and client remarks tracking, and improves bookkeeping operations through organized recordkeeping, descriptive analytics, and rule-based predictive forecasting indicators.

Specifically, the study aims to:

1. **Design and implement a centralized and secure client profile management module** that stores essential business and taxpayer information, supports Taxpayer Identification Number (TIN)-based search, and enforces role-based access control for authorized bookkeeper accounts.

2. **Develop a financial records management module** that organizes encoded BIR transactions, period-based financial entries, and generates structured financial totals and summaries for client transaction entry.

3. **Develop a Financial Analytics Engine** that summarizes sales, expenses, and tax-related records, presents descriptive financial trends and monthly summaries, and generates rule-based predictive forecasting indicators for sales, expenses, and tax based on recorded financial movement.

4. **Implement client remarks and compliance monitoring** that tracks client activity status (new, active, separated, closed), highlights filing status (filed, pending, late), and supports follow-up for bookkeepers.

5. **Create an integrated dashboard and reporting interface** that presents financial summaries, compliance monitoring information, client remarks insights, predictive forecasting indicators, and printable reports to support bookkeeping operations and decision-making.

## Panel Q&A (Objective Clarifications)

1. **What are the Predictive Forecasting Indicators, and where are they shown?**
	- The indicators are the **next-period expected values** (Sales, Expenses, Tax), the **next period label** (monthly/quarterly/annual), the **confidence level**, and the **forecast trend sparkline** shown in the **Analytics page** under Predictive Analytics Forecasting.

2. **Objective 5 says the dashboard and reports present predictive forecasting indicators, but I only see them in Analytics. Why?**
	- In the system, the **predictive indicators are presented in the Analytics module**, which is part of the overall reporting/analytics interface. They are **not displayed on the main dashboard cards**, so the accurate claim is that **predictive indicators appear in Analytics**, not the dashboard summary widgets.

3. **Objective 4 says it supports follow-up for bookkeepers. What does that mean?**
	- The system **tags clients by remarks** (new, active, separated, closed) and **flags compliance status** (filed, pending, late). These labels and counts **help bookkeepers prioritize follow-ups**, especially for clients who are pending or late.
