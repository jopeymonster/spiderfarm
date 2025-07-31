# The Spider Farm

![alt text](/spider_farm1.jpg "A rancher tends to his webcrawlers.")

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Usage](#usage)
- [License](#license)
- [Contact](#contact)

## Description

A collection of spiders using the [Scrapy](https://scrapy.org) web crawling framework.

## Features

![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![Scrapy](https://img.shields.io/badge/Built%20With-Scrapy-brightgreen.svg)
![CLI Tool](https://img.shields.io/badge/CLI-Enabled-orange.svg)

### LinkSpider

A configuable web crawler designed for link discovery and cataloging.

* **Recursive crawling** with optional crawl depth
* **Targeted link discovery** by specifying HTML tag and attribute (e.g., `a[href]`, `link[href]`, etc.)
* **Scoped content extraction** using container tags like `div.article` or `div#main`
* **Include / Exclude filtering** for links based on substrings (e.g., only crawl URLs containing `nike`, exclude those with `sale`)
* **Metadata extraction** from each page (`title`, `meta description`, `canonical link`)
* **Duplicate-awareness** avoids re-processing links from the same source page
* **Domain-restricted crawling** to seed domain and subdomains only
* **CSV export** or terminal table view of crawl results
* **CLI interface** with options for automation, logging level, and filename customization
* **Non-HTML resource filtering** (skips images, PDFs, scripts, etc.)
* **Safe and unique filename generation** using timestamp and seed URL

## Usage

```bash
python main.py --url https://example.com \
               --tag a \
               --attr href \
               --ctag div#main \
               --depth 3 \
               --log INFO \
               --auto save \
               --output my_links \
               --include nike,adidas \
               --exclude sale,outlet
```

### Available CLI Options

| Option      | Description                                                                   | Default      |
| ----------- | ----------------------------------------------------------------------------- | ------------ |
| `--url`     | Starting URL to crawl                                                         | *(required)* |
| `--tag`     | HTML tag to search for (`a`, `link`, etc.)                                    | `a`          |
| `--attr`    | Attribute from which to extract links                                         | `href`       |
| `--ctag`    | Optional container tag selector (`div.article`, `div#main`)                   | *(optional)* |
| `--depth`   | Maximum crawl depth (`0` = infinite)                                          | `2`          |
| `--log`     | Log verbosity: `NONE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`        | `INFO`       |
| `--auto`    | Auto output mode: `save` (CSV), `view` (table), or omit to be prompted        | *(optional)* |
| `--output`  | Custom output file name (no extension needed, `.csv` is added automatically)  | *(optional)* |
| `--include` | Comma-separated values that must appear in URL (case-insensitive)             | *(optional)* |
| `--exclude` | Comma-separated values that will **exclude** matching URLs (case-insensitive) | *(optional)* |


## Licenses

This project is licensed under the [MIT License](LICENSE).

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

### Third-Party Licenses

This project uses [Scrapy](https://scrapy.org), an open-source web crawling framework licensed under the [BSD 3-Clause License](https://github.com/scrapy/scrapy/blob/master/LICENSE).  
Copyright (c) Scrapy developers.

The full license text is included in the [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) file.

## Contact

- Joe Thompson (@jopeymonster)  
- https://github.com/jopeymonster
