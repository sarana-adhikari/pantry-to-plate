# 🍳 Pantry-to-Plate: AI-Powered Serverless Chef

A cloud-native, product-focused application that leverages Generative AI to solve the "what's for dinner" problem. This project serves as a technical bridge between enterprise-level cloud support and modern Cloud DevOps engineering.

## 🏗️ Technical Architecture

This project demonstrates a full-stack, serverless lifecycle: from **Infrastructure as Code (Terraform)** to **Event-Driven Backend (AWS Lambda)**, **Generative AI Integration (Gemini)**, and more.

The application follows a strictly decoupled, serverless architecture to ensure zero idle costs and high scalability.

* **Frontend:** A responsive web interface hosted on AWS.
* **API Gateway:** Acts as the public entry point, routing HTTP POST requests to the backend.
* **AWS Lambda (Python):** The core compute engine. It performs context management, prompt engineering, and interacts with the LLM.
* **Generative AI:** Integrated via the Google Gemini API (using the `gemini-flash-latest` model slug/alias).
* **Infrastructure:** 100% provisioned via Terraform onto AWS with a focus on security and observability.

## 🛠️ Tech Stack
* **Cloud:** AWS (Lambda, API Gateway, CloudWatch, IAM)
* **IaC:** Terraform
* **Languages:** Python 3.10+, HCL
* **AI/LLM:** Google Gemini API
* **CI/CD:** GitHub Actions

## 🌟 Key Engineering Features
* **Context Optimization:** Implemented system-level instructions (system prompt) to constrain LLM output, ensuring high-quality, relevant recipe generation while minimizing token usage.
* **Observability:** Provisioned custom CloudWatch Log Groups via Terraform with a 14-day retention policy to balance debugging needs with cost-optimization.
* **State Management:** Successfully managed real-world "State Drift" using `terraform import` to reconcile manually created AWS resources with the state file.
* **Future-Proofing:** Utilized AI model aliases/slugs to ensure the backend remains functional as Google updates their underlying LLM versions.

## 📂 Repository Structure
```text
.
├── infra/               # Terraform configuration files (.tf)
├── src/                 # Python backend logic (AWS Lambda handler)
├── frontend/            # HTML/CSS/JS web assets (Coming Soon)
├── .github/workflows/   # CI/CD pipeline definitions
└── README.md            # You are here!