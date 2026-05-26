
# SafeBooks: A Secure Financial Records Monitoring System with Tax Compliance Tracking and Predictive Risk Analytics


# CHAPTER 1

# INTRODUCTION

## Background of the Study

Managing financial records and fulfilling tax compliance obligations for multiple client businesses simultaneously has become an increasingly complex responsibility for bookkeeping professionals worldwide. As the number of client businesses they manage grows, so does the volume of financial transactions, tax figures, and tax authority requirements that must be accurately recorded, monitored, and processed on behalf of each client. Studies have demonstrated that the absence of structured financial record management systems directly affects the accuracy, consistency, and growth potential of business financial operations [1]. Without digital tools that consolidate client records, financial tracking, and compliance monitoring into a single organized platform, bookkeeping professionals are forced to rely on manual methods that are prone to errors, inconsistencies, and missed financial obligations.

The Philippine government has been actively advancing digital transformation in tax administration through the Bureau of Internal Revenue, which has expanded its digital platforms including the Electronic Filing and Payment System, eBIRForms, and the Online Registration and Update System to modernize tax filing and payment processes for businesses nationwide [2]. While these platforms have significantly improved tax administration at the government level, bookkeepers who assist client businesses in navigating BIR requirements continue to manage their own client records and compliance monitoring through manual and disconnected methods. This creates a persistent gap between the availability of government digital tax platforms and the actual tools that bookkeeping professionals use to manage their clients' financial data daily.

This study directly supports United Nations Sustainable Development Goal 9: Industry, Innovation and Infrastructure, which promotes the development of technology-driven solutions that advance digital innovation and strengthen productive capacity across industries [3]. It is likewise anchored on the Davao del Norte State College Research, Development, and Extension Agenda under its Strategic Development Plan 2025 to 2029, which emphasizes technology-driven community solutions that contribute to regional socio-economic development [4].

Home-based bookkeepers in Panabo City, Davao del Norte serve as both financial recorders and tax compliance assistants, managing monthly financial transactions, computing tax obligations, and processing BIR requirements for multiple client businesses simultaneously. These bookkeepers currently rely on a paper-based folder system where each folder contains all financial records and BIR-related information for a specific client business. When tax due dates approach, locating the correct client record becomes time-consuming and inefficient, particularly when clients share similar names or when one client owns multiple businesses. Since no mechanism exists for fast record retrieval, bookkeepers must check records manually to locate the correct business, causing delays that affect the timely processing of client tax obligations. The absence of a Taxpayer Identification Number-based search function is a significant gap, as the TIN is a unique identifier that could allow bookkeepers to locate the exact business record they need quickly and accurately.

Beyond record retrieval, the current approach creates deeper analytical gaps. Monthly financial and compliance data are recorded inconsistently across paper documents with no organized history. Without a financial analytics engine, bookkeepers cannot identify meaningful trends in their clients' financial data. The lack of a risk classification mechanism means there is no systematic way to determine which client businesses are financially stable or at risk. Most critically, the absence of any forecasting capability means potential financial concerns can only be recognized after problems have already emerged, limiting the bookkeeper's ability to provide timely and proactive advisory support. Additionally, sensitive client information including TIN numbers, BIR credentials, and financial records stored in physical documents remain entirely unprotected due to the absence of any security mechanism.

To address these challenges, this study proposes **SafeBooks: A Secure Financial Records Monitoring System with Tax Compliance Tracking and Predictive Risk Analytics**. The system centralizes client profile and monthly financial record management, enables TIN-based search for faster and more accurate record retrieval, and applies descriptive and predictive analytics to generate financial trend summaries and forecast each client business's projected financial direction. It incorporates a rule-based risk classification system that categorizes each client business as Low, Medium, or High Risk with corresponding advisory notes, and implements secure user authentication to protect sensitive client financial and BIR information. The system will be evaluated through assessments of usability, functional accuracy, and effectiveness in supporting financial monitoring and advisory decision-making among the target users.

---

# Objectives of the Study

The primary objective of this study is to develop **SafeBooks: A Secure Financial Records Monitoring System with Tax Compliance Tracking and Predictive Risk Analytics** that centralizes client financial record management, supports tax compliance monitoring, and enables data-driven advisory decision-making through descriptive analytics, predictive forecasting, and automated risk classification.

Specifically, the study aims to:

1. Design and implement a centralized and secure client profile management module for storing and managing client business profiles and BIR-related information.

2. Develop a monthly financial records tracking module that records and organizes financial and tax compliance data for each client business per period.

3. Build a Financial Analytics Engine that processes recorded financial data to perform descriptive analysis of historical financial trends and predictive forecasting of each client business's projected financial direction.

4. Incorporate a rule-based risk classification system that evaluates analyzed financial and compliance trend patterns to classify each client business as Low, Medium, or High Risk with corresponding advisory notes.

5. Create an integrated dashboard that presents risk classifications, financial trend summaries, forecasting insights, compliance statuses, and generates organized reports in a clear and actionable format.

---

# Significance of the Study

This study develops **SafeBooks: A Secure Financial Records Monitoring System with Tax Compliance Tracking and Predictive Risk Analytics** to support bookkeeping professionals in managing client financial records, monitoring tax compliance obligations, and making informed advisory decisions through analytics and risk classification. The findings and outcomes of this study are expected to provide direct and meaningful value to the following stakeholders:

### Bookkeepers

As the primary users of the system, bookkeepers will benefit most from its development. The system addresses the core difficulty of managing multiple client financial records simultaneously by providing a centralized platform where client profiles, monthly financial data, and BIR compliance information are organized and accessible. The addition of predictive forecasting allows bookkeepers to anticipate potential financial concerns in their clients' businesses before problems arise, strengthening their capacity to deliver proactive and well-informed advisory support. Risk classification insights and organized report generation further enhance the quality and professionalism of the services they provide.

### Client Businesses

Businesses whose financial records are managed by bookkeepers will benefit from more accurate, consistent, and organized financial record management. With compliance statuses properly tracked and financial data systematically recorded, client businesses are less exposed to risks associated with missed tax obligations, inaccurate filings, and overlooked BIR requirements. The predictive risk classification feature also means that financial concerns within their business operations can be identified and addressed earlier than would be possible under the current manual approach.

### Local Bookkeeping Organization

The bookkeeping organization to which the target users are affiliated will benefit indirectly as its member bookkeepers improve the quality and efficiency of their financial monitoring and advisory services through the system. The structured reports and analytics generated by SafeBooks can also serve as a reference for the organization in developing training programs, establishing best practices, and promoting higher standards of financial record management among its members and the local business community they serve.

---

# Scope and Limitation

The system is designed for home-based bookkeepers affiliated with a bookkeeping organization in Panabo City, Davao del Norte, as the primary users who will input, manage, and monitor client financial and compliance records through the platform. The evaluation of the system will involve these same target users to assess its usability and effectiveness in supporting their financial monitoring and advisory responsibilities.

The proposed system is implemented as a web-based platform developed using standard web development technologies, accessible through common laptops or desktop computers typically used in home or office computing environments. It integrates a client profile management module, a monthly financial records tracking module, a Financial Analytics Engine, a rule-based risk classification system, an integrated dashboard, and secure user authentication to protect sensitive client financial and BIR information. The platform does not require specialized hardware or high-end server infrastructure, making it practical for the operational setup of the target users.

The system manages client business profiles containing taxpayer details and BIR-related information, together with monthly financial and tax compliance data manually encoded by bookkeepers. These records serve as the primary dataset for financial tracking, analytics, risk classification, and forecasting, with data validation mechanisms applied during input to promote completeness and consistency of stored information.

The system processes entered data through its analytical components to support financial monitoring and advisory decision-making. The Financial Analytics Engine applies descriptive analysis to summarize historical financial trends and predictive forecasting to project each client business's financial direction for the upcoming period based on recorded patterns. The rule-based risk classification system evaluates the analyzed data to classify each client business as Low, Medium, or High Risk with corresponding advisory notes, all presented through an integrated dashboard that also generates organized reports for bookkeeper reference.

The system is intended only for home-based bookkeepers affiliated with the identified bookkeeping organization in Panabo City and is not designed for government agencies, accounting firms, or organizations outside the identified user group.

The system operates as a prototype without machine learning, artificial intelligence, or direct integration with external BIR platforms such as the Electronic Filing and Payment System, eBIRForms, or the Online Registration and Update System. It does not require and does not support specialized hardware or high-end server configurations beyond what is typically available in a standard home or office computing environment.

The system relies solely on manually entered records, meaning the accuracy and reliability of all outputs including financial trend summaries, forecasting projections, and risk classifications depend entirely on the completeness and correctness of the data submitted by the bookkeeper. The system records tax figures as entered by bookkeepers but does not automatically compute tax amounts.

All risk classifications and forecasting outputs are based solely on predefined rules and recorded financial patterns rather than probabilistic models. The system does not perform full accounting functions, and its analytical outputs are limited to the scope of data entered into the platform and the rules defined within the system.

---

# Review of Related Literature and Works

## Related Literature

The increasing complexity of financial record management and tax compliance has led to the growing adoption of digital systems that support more structured and efficient financial practices. This review examines literature related to financial record management, tax compliance, digital bookkeeping systems, and financial analytics to establish the foundation of the present study.

Effective financial record management plays a vital role in maintaining business stability and supporting decision-making. Studies have shown that businesses relying on disorganized and manual recordkeeping are more prone to financial inconsistencies and compliance issues. According to Mintah et al. [1], structured financial record management significantly contributes to improved business performance and financial planning, particularly among small and micro-enterprises.

The digitalization of tax compliance processes has also been recognized as a key factor in improving reporting accuracy and efficiency. Okunogbe and Pouliquen [5] found that digital tax systems enhance compliance rates and reduce administrative burden. However, these systems are primarily designed for direct business use, with limited support for bookkeeping professionals managing multiple client accounts.

Advancements in technology have further influenced accounting and bookkeeping practices. Moll and Yigitbasioglu [6] highlighted that digital tools improve financial visibility and enable more timely monitoring of financial activities. These capabilities are essential for bookkeepers handling multiple clients, where centralized access to financial data is necessary.

The integration of financial analytics into accounting systems has been widely explored as a means of enhancing decision-making. Appelbaum et al. [7] emphasized the importance of combining descriptive and predictive analytics to generate meaningful financial insights. Similarly, Warren et al. [8] noted that analytics allows practitioners to identify trends and anticipate future financial outcomes, supporting more proactive financial management.

Forecasting techniques based on financial trends have also been proven effective in projecting future performance. Horak et al. [10] demonstrated that trend-based forecasting provides practical and interpretable results, making it suitable for financial applications that require simplicity and clarity for end users.

In addition, risk classification based on financial data has been used to assess the financial condition of business entities. Delen et al. [9] showed that classification approaches can effectively categorize financial performance and support early identification of potential risks. However, such approaches are commonly applied in corporate and banking contexts, with limited application in bookkeeping environments.

A synthesis of the reviewed literature reveals that while existing studies highlight the importance of digital record management, tax compliance systems, financial analytics, forecasting, and risk classification, these components are often implemented separately. There is a lack of integrated systems specifically designed for bookkeeping professionals managing multiple clients. This gap supports the development of SafeBooks, which aims to combine these functionalities into a single, centralized, and secure platform.

---

# Definition of Terms

### Advisory Decision-Making

Refers to the process by which bookkeepers analyze financial data and system-generated insights to provide informed recommendations to client businesses.

### Client Profile Management

Refers to the system module responsible for storing, organizing, and maintaining client business information, including taxpayer details and Bureau of Internal Revenue (BIR)-related data.

### Dashboard

Refers to the graphical user interface of the system that presents financial summaries, risk classifications, compliance statuses, and forecasting insights in an organized and user-friendly format.

### Descriptive Analytics

Refers to the process of analyzing historical financial data to identify patterns and summarize past financial performance of client businesses.

### Financial Analytics Engine

Refers to the core component of the system that processes recorded financial data to generate descriptive insights and predictive forecasts for each client business.

### Financial Records Tracking

Refers to the systematic recording and organization of monthly financial transactions and tax-related data for each client business within the system.

### Forecasting

Refers to the system’s capability to project the future financial direction of a client business based on historical financial data and observed trends.

### Integrated Reporting

Refers to the system’s ability to generate structured and organized reports that combine financial data, compliance status, risk classification, and analytical insights.

### Risk Classification

Refers to the rule-based process of categorizing client businesses into Low, Medium, or High Risk based on analyzed financial and compliance data patterns.

### Secure Authentication

Refers to the security mechanism that ensures only authorized users can access the system and its stored financial and client information.

### Tax Compliance Monitoring

Refers to the process of tracking and managing client business obligations related to tax filing, payment deadlines, and BIR requirements.

### Taxpayer Identification Number (TIN)

Refers to the unique identifier assigned to each taxpayer, used in the system to accurately search and retrieve specific client business records.

### TIN-Based Search

Refers to the system feature that allows users to quickly locate client records using the Taxpayer Identification Number as a unique search key.

### Web-Based System

Refers to the platform architecture of SafeBooks, which is accessible through web browsers on standard computing devices without requiring specialized software installation.


# References

[1] C. Mintah, M. Gabir, F. Aloo, and E. K. Ofori, "Do business records management affect business growth?" *PLOS ONE*, vol. 17, no. 3, p. e0264135, Mar. 2022. [Online]. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC8912245/. [Accessed: Mar. 2026].

[2] Bureau of Internal Revenue, "Strategic Plan 2024-2028," *BIR Official Website*, 2024. [Online]. Available: https://bir-cdn.bir.gov.ph/BIR/pdf/Strategic%20Plan%20Annex%20A.pdf. [Accessed: Mar. 05, 2026].

[3] United Nations Department of Economic and Social Affairs, "Transforming our world: The 2030 Agenda for Sustainable Development," [Online]. Available: https://sdgs.un.org/2030agenda. [Accessed: Mar. 05, 2026].

[4] Davao del Norte State College, "DNSC PRMO facilitates 2nd workshop on the development of the DNSC Strategic Plan 2025-2029," *DNSC Official Website*, May 2024. [Online]. Available: https://dnsc.edu.ph/dnsc-prmo-facilitates-2nd-workshop-on-the-development-of-the-dnsc-strategic-plan-2025-2029. [Accessed: Mar. 05, 2026].

[5] O. Okunogbe and V. Pouliquen, "Technology, Taxation, and Corruption: Evidence from the Introduction of Electronic Tax Filing," *American Economic Journal: Economic Policy*, vol. 14, no. 1, pp. 341-372, Feb. 2022. [Online]. Available: https://www.aeaweb.org/articles?id=10.1257/pol.20200123. [Accessed: Apr. 2026].

[6] J. Moll and O. Yigitbasioglu, "The role of internet-related technologies in shaping the work of accountants: New directions for accounting research," *The British Accounting Review*, vol. 51, no. 6, p. 100833, 2019. [Online]. Available: https://www.sciencedirect.com/science/article/abs/pii/S0890838919300459. [Accessed: Apr. 2026].

[7] D. Appelbaum, A. Kogan, M. Vasarhelyi, and Z. Yan, "Impact of business analytics and enterprise systems on managerial accounting," *International Journal of Accounting Information Systems*, vol. 25, pp. 29-44, May 2017. [Online]. Available: https://www.sciencedirect.com/science/article/abs/pii/S1467089517300490. [Accessed: Apr. 2026].

[8] J. D. Warren, K. C. Moffitt, and P. Byrnes, "How Big Data Will Change Accounting," *Accounting Horizons*, vol. 29, no. 2, pp. 397-407, Jun. 2015. [Online]. Available: https://publications.aaahq.org/accounting-horizons/article-abstract/29/2/397/2168. [Accessed: Apr. 2026].

[9] D. Delen, C. Kuzey, and A. Uyar, "Measuring firm performance using financial ratios: A decision tree approach," *Expert Systems with Applications*, vol. 40, no. 10, pp. 3970-3983, Aug. 2013. [Online]. Available: https://www.sciencedirect.com/science/article/abs/pii/S0957417413000158. [Accessed: Apr. 2026].