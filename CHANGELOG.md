# Changelog

All notable changes to the **FHOC – Fighting Harmful Online Communication** tool are documented here.

---

## 2026-03-30

### ✨ New Features

- **Debunk Analysis**: New module that detects and explains climate misinformation using the FLICC framework (Fake Experts, Logical Fallacies, Impossible Expectations, Cherry Picking, Conspiracy Theories) and CARDS categories. Results are displayed with visual icons for each technique.

- **Narrative Media Framing**: New analysis module that identifies how climate stories are framed in media — including conflict framing and cultural story angles — and renders explanations in the app.

- **CARDS Classification**: Integrated DiscourseLab's API for fine-grained text classification into climate communication categories.

- **URL & PDF Input Support**: The tool now accepts article URLs and PDF files as direct inputs for both debunking and narrative framing analysis.

- **Result Caching**: Analysis results are now cached based on the input source, so re-submitting the same article or PDF is near-instant.

### 🔧 Improvements

- **Faster Debunk Processing**: Rewrote the debunk workflow for significantly better performance and cleaner internal structure.

- **Upgraded LLM Backend**: Switched to OpenRouter (via `langchain-openrouter`) for more flexible and cost-effective model routing.

- **Better PDF Handling**: Improved PDF-to-markdown conversion for higher compatibility across document formats.

- **Improved UI Theme**: Applied a custom CSS theme and styling at app launch for a more polished look, including styled text containers and misinformation highlights.

- **Concurrent Processing**: Analysis now runs classification tasks concurrently with `asyncio`, reducing wait times for multi-chunk articles.

- **Robust Error Handling**: Handler now recovers gracefully from failed URL fetches and edge-case inputs.

### 🐛 Fixes

- Fixed narrative label rendering that was displaying incorrectly in the HTML output.

- Fixed narrative explanation formatting for conflict and cultural story cards.

- Fixed URL processing function to return an empty result instead of crashing on failure.

- Corrected narrative label assignments that were mismatched in certain framing categories.

---

## [Initial Release] – 2026-02-17

### ✨ New Features

- **Misinformation Detection**: Core pipeline for detecting climate misinformation fallacies in text using a classification model.

- **Gradio Web Interface**: Interactive web app for submitting articles and viewing analysis results.

- **Rebuttal Generation**: LLM-powered generation of rebuttals for detected misinformation claims.

- **Text Chunking**: Utility for splitting long articles into manageable chunks for classification.

### 🔧 Improvements

- Initial dependency setup with PyTorch (CPU), Gradio, and supporting NLP libraries.

---

*This project is part of the University of Melbourne Hallmark Research Initiative on "Fighting Harmful Online Communication."*
