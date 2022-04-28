# theBrowser :zap:

![build](https://github.com/aaralh/theBrowser/workflows/CI-Build/badge.svg)


Browser made completely(or as much as possible) with Python and complies with the [HTML spec](https://html.spec.whatwg.org).

## Setup dev environment

1. Check that you have Python 3.8 or newer installed
2. Clone the repo from git ```git clone https://github.com/aaralh/theBrowser.git```
3. Make python virtual env with ```python3 -m venv theBrowser``` and activate it ```source theBrowser/bin/activate```
4. Install dependencies by running ```pip install -r requirements.txt```
5. To run mypy and unit tests, execute ```./test.sh```
6. Happy hacking! :)

## Features

Bolded items with :construction: are currently in WIP. Items marked with :shipit: are working but may be partially lacking, hence not considerable as finished yet. Completed features are marked with :rocket: List will be extended in more detail on the go.

- [ ] 📝 **HTML Parsing**:shipit:
    - [ ] **HTML tokenizer**:shipit:
    - [ ] **HTML parser**:shipit:
- [ ] 📝 **CSS Parsing**:shipit:
    - [ ] **CSS tokenizer**:shipit:
    - [ ] **CSS parser** :shipit:
- [ ] 📐 Style
    - [ ] **CSS cascade** :construction:
    - [ ] **Style computation** :construction:
    - [ ] **Render tree** :construction:
    - [ ] **Selector matching** :construction:
- [ ] 🎴 Layout process
    - [ ] **Layouts** 
      - [ ] **Table**:shipit:
      - [ ] **Block**:construction:
      - [ ] **Flex**:construction:
      - [ ] **Grid**:construction:
- [ ] 🎨 **Rendering**:construction:
- [ ] 🌍 **Networking**:construction:
- [ ] 🖼️ **Media**:construction:
- [ ] JavaScript
