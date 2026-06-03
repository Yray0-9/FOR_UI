# SAFEBOOKS Enhancement Plan and Panel Feedback Analysis

## Project Title

**SAFEBOOKS: A Web-Based Bookkeeping Platform for Client Transaction Entry Records with Financial Analytics and Forecasting Insights**

---

# 1. Current Assessment of the Project

The SAFEBOOKS platform already provides core bookkeeping functionalities, including:

* Client profile management
* Financial transaction entry
* Compliance monitoring
* Financial analytics dashboard
* Financial summary reporting
* Forecasting insight section

The project successfully addresses bookkeeping record management and provides valuable financial information for bookkeepers and accounting staff.

However, based on the panel's feedback, the forecasting component requires further enhancement to demonstrate a stronger research and analytical contribution.

---

# 2. Understanding the Panel's Feedback

The panel noted that the current forecasting implementation appears to be based primarily on historical summaries and weighted averages.

Current Process:

Historical Transactions
→ Monthly Totals
→ Weighted Average
→ Expected Sales/Expenses/Tax

The panel considers this approach closer to:

* Descriptive Analytics
* Trend Visualization
* Historical Analysis

rather than a true forecasting model.

The primary concern is that the forecasting output lacks a clear evaluation of forecasting methodologies and does not demonstrate why a particular forecasting technique was selected.

---

# 3. Difference Between Descriptive Analytics and Forecasting

## Descriptive Analytics

Descriptive analytics answers:

**"What happened?"**

Examples already present in SAFEBOOKS:

* Total Sales
* Total Expenses
* Total Tax
* Net Value
* Monthly Trends
* Compliance Status
* Client Financial Summaries

These features are valid and should remain part of the project.

---

## Forecasting (Predictive Analytics)

Forecasting answers:

**"What is likely to happen?"**

Examples:

* Predicted Sales for Next Quarter
* Predicted Expenses for Next Quarter
* Predicted Tax Obligations
* Predicted Annual Financial Performance

Forecasting requires the use of a forecasting algorithm that generates future projections based on historical data.

---

# 4. Recommended Forecasting Study

To strengthen the forecasting component, compare three forecasting algorithms.

## Algorithm 1: Moving Average

Uses the average of previous periods to estimate future values.

Advantages:

* Easy to implement
* Easy to explain

Limitations:

* Does not capture long-term trends effectively

---

## Algorithm 2: Weighted Moving Average

Assigns higher importance to recent financial records.

Advantages:

* More responsive to recent changes

Limitations:

* Still limited in identifying long-term patterns

---

## Algorithm 3: Linear Regression

Uses historical trends to project future values.

Advantages:

* Suitable for long-term forecasting
* Effective for trend analysis
* Appropriate for datasets with multiple years of records

Limitations:

* Assumes trend continuity

---

# 5. Algorithm Evaluation

Use historical client transaction records.

Example:

2021 Data
2022 Data
2023 Data
2024 Data
2025 Data

Compare forecasting accuracy using:

* MAE (Mean Absolute Error)
* MAPE (Mean Absolute Percentage Error)
* RMSE (Root Mean Square Error)

The algorithm with the best forecasting accuracy will be selected and integrated into SAFEBOOKS.

Research Process:

Historical Data
→ Algorithm Comparison
→ Accuracy Evaluation
→ Best Algorithm Selection
→ Final Forecasting Module

This creates a clear research contribution for the capstone project.

---

# 6. Recommended Forecasting Module Enhancements

## Forecasting Filters

The forecasting page should allow users to generate forecasts dynamically.

Suggested Filters:

* Client Filter
* Date Range Filter
* Forecast Type Filter

  * Sales
  * Expenses
  * Taxes
* Forecast Horizon Filter

  * 3 Months
  * 6 Months
  * 12 Months
  * 1 Year

Benefits:

* More interactive forecasting
* Better decision support
* Greater analytical flexibility

---

# 7. Recommended Forecasting Outputs

The forecasting module should provide multiple outputs rather than a single prediction card.

## Forecast Summary

Displays:

* Forecasted Sales
* Forecasted Expenses
* Forecasted Tax
* Forecasted Net Value

---

## Forecast Table

Example:

| Period        | Forecasted Sales |
| ------------- | ---------------- |
| January 2026  | ₱100,000         |
| February 2026 | ₱105,000         |
| March 2026    | ₱110,000         |

---

## Actual vs Forecast Report

Displays:

* Historical Values
* Forecasted Values
* Forecast Accuracy

Purpose:

Allows users to compare projections against actual financial performance.

---

## Forecast Accuracy Report

Displays:

| Algorithm               | Accuracy |
| ----------------------- | -------- |
| Moving Average          | 82%      |
| Weighted Moving Average | 87%      |
| Linear Regression       | 92%      |

Purpose:

Justifies the selection of the forecasting algorithm.

---

# 8. Additional Descriptive Analytics Reports

The panel suggested adding more reports.

This does not necessarily mean adding more graphs.

Recommended reports include:

## Financial Summary Report

Displays:

* Total Sales
* Total Expenses
* Total Tax
* Net Value

---

## Client Performance Report

Displays:

* Top Revenue Clients
* Most Active Clients
* Highest Tax-Contributing Clients

---

## Tax Summary Report

Displays:

* Monthly Tax Totals
* Quarterly Tax Totals
* Annual Tax Totals

---

## Expense Analysis Report

Displays:

* Expense Trends
* Expense Categories
* Expense Growth Rates

---

## Sales Analysis Report

Displays:

* Monthly Sales
* Quarterly Sales
* Annual Sales

---

# 9. Graph Recommendations

Not every report requires a graph.

Recommended graph usage:

### Monthly Sales Trend

Graph Recommended

### Expense Trend

Graph Recommended

### Tax Trend

Graph Recommended

### Forecast Trend

Graph Recommended

### Financial Summary

Cards or Tables Preferred

### Client Performance Report

Table Preferred

### Tax Summary Report

Table Preferred

### Forecast Accuracy Report

Table Preferred

The goal is to present meaningful information rather than increasing the number of charts.

---

# 10. Proposed Analytics Structure

## Financial Analytics Dashboard

### Summary Cards

* Total Sales
* Total Expenses
* Total Tax
* Net Value

### Trend Reports

* Monthly Sales Trend
* Monthly Expense Trend
* Monthly Tax Trend

### Financial Reports

* Client Performance Report
* Expense Analysis Report
* Tax Analysis Report

### Forecasting Reports

* Forecast Summary
* Forecast Table
* Actual vs Forecast Comparison
* Forecast Accuracy Report

---

# 11. Final Recommendation

The current SAFEBOOKS platform already demonstrates a strong bookkeeping foundation.

The project should focus on:

1. Maintaining existing descriptive analytics features.
2. Expanding reporting capabilities.
3. Implementing forecasting algorithm comparison.
4. Selecting the most accurate forecasting algorithm.
5. Adding forecasting filters.
6. Providing multiple forecasting outputs.
7. Demonstrating the use of long-term historical data for future projections.

These enhancements directly address the concerns raised by the panel and strengthen both the research contribution and practical value of the SAFEBOOKS platform.
