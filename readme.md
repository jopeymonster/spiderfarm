# The Spider Farm

![alt text](/spider_farm1.jpg "A rancher tends to his webcrawlers.")

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Usage](#usage)
- [License](#license)
- [Contact](#contact)

## Description

A collection of spiders built on the [Scrapy](https://scrapy.org) framework, designed for targeted link discovery, schema extraction, and dynamic content crawling using **Playwright**.

---

## Features

![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![Scrapy](https://img.shields.io/badge/Built%20With-Scrapy-brightgreen.svg)
![Playwright](https://img.shields.io/badge/JS%20Rendering-Playwright-ff69b4.svg)
![CLI Tool](https://img.shields.io/badge/CLI-Enabled-orange.svg)

---

### **Playwright Integration**
- Handles **JavaScript-rendered pages** directly inside Scrapy.
- Supports custom **navigation waits** (`domcontentloaded`, `networkidle`, etc.).
- Passes **custom headers** (e.g., Google referer spoofing) to bypass basic bot protection.
- Works seamlessly with both **LinkSpider** and **SchemaSpider** via `meta` configuration.
- Uses Scrapy’s `DOWNLOAD_HANDLERS` for Playwright — no manual middleware configuration needed.

---

### **LinkSpider**
A configurable web crawler for link discovery and cataloging.

* **Recursive crawling option** with custom or infinite crawl depth.
* **Targeted link discovery** by specifying HTML tag and attribute (e.g., `a[href]`, `link[href]`).
* **Scoped content extraction** using container tags like `div.article` or `div#main`.
* **Include / Exclude filtering** for URLs (e.g., include `nike`, exclude `sale`).
* **Metadata extraction** from each page (`title`, `meta description`, `canonical link`).
* **Non-HTML resource filtering** to skip images, PDFs, scripts, etc.
* **Duplicate-awareness** to avoid reprocessing the same links.
* **Domain-restricted crawling** to the seed domain and its subdomains.
* **CSV export** or **terminal table** output.
* **CLI interface** for automation, logging control, and filename customization.

---

### **SchemaSpider**
Everything in **LinkSpider**, plus:

* **Automatic Schema.org structured data extraction**:
  - Supports `JSON-LD`, COMING SOON = `Microdata`, and `RDFa`.
  - Normalizes schema output for analysis.
* **Playwright-powered schema crawling**:
  - Loads JavaScript-heavy pages to reveal client-side schema markup.
* **Recursive schema discovery**:
  - Optionally follows links and extracts schema data across multiple pages.
* **Auto-save or view modes**:
  - Save as CSV or inspect directly in terminal.

---

## Usage

### **Basic Example**
```bash
python main.py --url "https://example.com" \
               --tag a \
               --attr href \
               --ctag div#main \
               --depth 3 \
               --log INFO \
               --auto save \
               --output my_links \
               --include nike,adidas \
               --exclude sale,outlet
