# Worm Gear Calculator - Web Application Specification

## Overview

Browser-based interface using Pyodide to run the Python calculator in WebAssembly. Single-page app hosted on GitHub Pages.

**Status: Not yet implemented**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                             │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   index.html │  │   app.js    │  │    style.css    │ │
│  │   UI Layout  │  │  Pyodide    │  │    Styling      │ │
│  │             │  │  Bindings   │  │                 │ │
│  └─────────────┘  └──────┬──────┘  └─────────────────┘ │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────────┐│
│  │                    Pyodide                          ││
│  │  ┌─────────────────────────────────────────────┐   ││
│  │  │              wormcalc (Python)              │   ││
│  │  │  core.py | validation.py | output.py       │   ││
│  │  └─────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### No Build Step

Static HTML/JS/CSS only. No webpack, no npm, no build process. Just files served by GitHub Pages.

### Pyodide for Python

The core library has zero dependencies (stdlib only), so it loads fast in Pyodide without needing to install packages.

### Progressive Enhancement

1. Show loading state while Pyodide initializes
2. Form works immediately after load
3. Calculate on input change (debounced)
4. Results update live

## User Interface

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Worm Gear Calculator                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Design Mode: [Envelope ▼]                              │
│                                                         │
│  ┌─────────────────────┐  ┌─────────────────────────┐  │
│  │ INPUTS              │  │ RESULTS                 │  │
│  │                     │  │                         │  │
│  │ Worm OD:  [20    ]  │  │ ═══ Worm Gear Design ═══│  │
│  │ Wheel OD: [65    ]  │  │ Ratio: 30:1             │  │
│  │ Ratio:    [30    ]  │  │ Module: 2.031 mm        │  │
│  │                     │  │                         │  │
│  │ ─── Options ───     │  │ Worm:                   │  │
│  │ Pressure ∠: [20 ]   │  │   Tip Ø: 20.00 mm      │  │
│  │ Backlash:   [0  ]   │  │   Pitch Ø: 15.94 mm    │  │
│  │ Starts:     [1  ]   │  │   Lead ∠: 7.3°         │  │
│  │ Hand: [Right ▼]     │  │                         │  │
│  │                     │  │ Wheel:                  │  │
│  └─────────────────────┘  │   Tip Ø: 65.00 mm      │  │
│                           │   Teeth: 30             │  │
│  ┌─────────────────────┐  │                         │  │
│  │ VALIDATION          │  │ Centre distance: 38.4mm│  │
│  │                     │  │ Efficiency: ~70%        │  │
│  │ ✓ Design valid      │  │ Self-locking: No        │  │
│  │                     │  │                         │  │
│  │ ℹ Module 2.031 is   │  └─────────────────────────┘  │
│  │   close to 2.0      │                               │
│  └─────────────────────┘  ┌─────────────────────────┐  │
│                           │ [Copy JSON] [Download MD]│  │
│                           └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Design Modes

Dropdown to select input mode:

1. **Envelope** - Both ODs and ratio
2. **From Wheel** - Wheel OD, ratio, target lead angle
3. **From Module** - Standard module, ratio
4. **From Centre Distance** - Centre distance, ratio

Form fields change based on selected mode.

### Validation Display

- **Errors**: Red background, ✗ icon
- **Warnings**: Amber background, ⚠ icon  
- **Info**: Blue background, ℹ icon
- **Valid**: Green checkmark

### Export Options

- **Copy JSON**: Copy to clipboard
- **Download MD**: Download as .md file
- **Copy Link**: URL with parameters encoded (for sharing)

## Implementation Plan

### File Structure

```
web/
├── index.html      # Single page app
├── app.js          # Pyodide loader, UI bindings
├── style.css       # Styling
└── wormcalc/       # Python package (copied from src/)
    ├── __init__.py
    ├── core.py
    ├── validation.py
    └── output.py
```

### index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Worm Gear Calculator</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>Worm Gear Calculator</h1>
        </header>
        
        <main>
            <section id="inputs">
                <label for="mode">Design Mode:</label>
                <select id="mode">
                    <option value="envelope">Envelope (both ODs)</option>
                    <option value="from-wheel">From Wheel OD</option>
                    <option value="from-module">From Module</option>
                    <option value="from-centre-distance">From Centre Distance</option>
                </select>
                
                <div id="mode-inputs">
                    <!-- Dynamic inputs based on mode -->
                </div>
                
                <details>
                    <summary>Options</summary>
                    <div id="options-inputs">
                        <!-- Pressure angle, backlash, etc. -->
                    </div>
                </details>
            </section>
            
            <section id="validation">
                <div id="validation-status"></div>
                <ul id="validation-messages"></ul>
            </section>
            
            <section id="results">
                <pre id="results-text"></pre>
            </section>
            
            <section id="export">
                <button id="copy-json">Copy JSON</button>
                <button id="download-md">Download Markdown</button>
            </section>
        </main>
        
        <div id="loading">
            Loading calculator...
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <script src="app.js"></script>
</body>
</html>
```

### app.js

```javascript
// Pyodide loader and UI bindings

let pyodide = null;
let wormcalc = null;

async function initPyodide() {
    // Show loading
    document.getElementById('loading').style.display = 'block';
    
    // Load Pyodide
    pyodide = await loadPyodide();
    
    // Load wormcalc package
    await pyodide.loadPackage('micropip');
    
    // Load local Python files
    const files = ['core.py', 'validation.py', 'output.py', '__init__.py'];
    for (const file of files) {
        const response = await fetch(`wormcalc/${file}`);
        const content = await response.text();
        pyodide.FS.writeFile(`/home/pyodide/wormcalc/${file}`, content);
    }
    
    // Import module
    await pyodide.runPythonAsync(`
        import sys
        sys.path.insert(0, '/home/pyodide')
        import wormcalc
    `);
    
    // Hide loading
    document.getElementById('loading').style.display = 'none';
    
    // Initial calculation
    calculate();
}

function calculate() {
    const mode = document.getElementById('mode').value;
    const inputs = getInputs(mode);
    
    const result = pyodide.runPython(`
        import json
        from wormcalc import ${getDesignFunction(mode)}, validate_design, to_json, to_summary
        
        design = ${getDesignFunction(mode)}(${formatArgs(inputs)})
        validation = validate_design(design)
        
        json.dumps({
            'summary': to_summary(design),
            'json': to_json(design, validation),
            'valid': validation.valid,
            'messages': [
                {'severity': m.severity.value, 'message': m.message, 'code': m.code}
                for m in validation.messages
            ]
        })
    `);
    
    const data = JSON.parse(result);
    updateUI(data);
}

function getInputs(mode) {
    // Read form inputs based on mode
    switch (mode) {
        case 'envelope':
            return {
                worm_od: parseFloat(document.getElementById('worm-od').value),
                wheel_od: parseFloat(document.getElementById('wheel-od').value),
                ratio: parseInt(document.getElementById('ratio').value),
                pressure_angle: parseFloat(document.getElementById('pressure-angle').value),
                backlash: parseFloat(document.getElementById('backlash').value),
                num_starts: parseInt(document.getElementById('num-starts').value),
            };
        // ... other modes
    }
}

function getDesignFunction(mode) {
    const functions = {
        'envelope': 'design_from_envelope',
        'from-wheel': 'design_from_wheel',
        'from-module': 'design_from_module',
        'from-centre-distance': 'design_from_centre_distance',
    };
    return functions[mode];
}

function updateUI(data) {
    // Update results
    document.getElementById('results-text').textContent = data.summary;
    
    // Update validation
    const statusEl = document.getElementById('validation-status');
    statusEl.textContent = data.valid ? '✓ Design valid' : '✗ Design has errors';
    statusEl.className = data.valid ? 'valid' : 'invalid';
    
    // Update messages
    const messagesEl = document.getElementById('validation-messages');
    messagesEl.innerHTML = data.messages.map(m => 
        `<li class="${m.severity}">${m.message}</li>`
    ).join('');
    
    // Store JSON for export
    window.designJson = data.json;
}

// Debounced input handler
let debounceTimer;
function onInputChange() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(calculate, 300);
}

// Export functions
function copyJson() {
    navigator.clipboard.writeText(window.designJson);
}

function downloadMarkdown() {
    const md = pyodide.runPython(`
        from wormcalc import to_markdown
        to_markdown(design, validation)
    `);
    
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'worm-gear-design.md';
    a.click();
}

// Initialize
document.addEventListener('DOMContentLoaded', initPyodide);
```

### style.css

```css
:root {
    --color-valid: #22c55e;
    --color-error: #ef4444;
    --color-warning: #f59e0b;
    --color-info: #3b82f6;
    --color-bg: #f8fafc;
    --color-surface: #ffffff;
    --color-text: #1e293b;
    --color-border: #e2e8f0;
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--color-bg);
    color: var(--color-text);
    line-height: 1.5;
    margin: 0;
    padding: 1rem;
}

#app {
    max-width: 900px;
    margin: 0 auto;
}

header h1 {
    margin: 0 0 1rem;
}

main {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

@media (max-width: 600px) {
    main {
        grid-template-columns: 1fr;
    }
}

section {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    padding: 1rem;
}

label {
    display: block;
    margin-bottom: 0.25rem;
    font-weight: 500;
}

input, select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--color-border);
    border-radius: 0.25rem;
    margin-bottom: 0.75rem;
}

input:focus, select:focus {
    outline: none;
    border-color: var(--color-info);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

#validation-status {
    font-weight: 600;
    margin-bottom: 0.5rem;
}

#validation-status.valid {
    color: var(--color-valid);
}

#validation-status.invalid {
    color: var(--color-error);
}

#validation-messages {
    list-style: none;
    padding: 0;
    margin: 0;
}

#validation-messages li {
    padding: 0.5rem;
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
}

#validation-messages li.error {
    background: #fef2f2;
    color: var(--color-error);
}

#validation-messages li.warning {
    background: #fffbeb;
    color: var(--color-warning);
}

#validation-messages li.info {
    background: #eff6ff;
    color: var(--color-info);
}

#results-text {
    font-family: 'SF Mono', Monaco, monospace;
    font-size: 0.875rem;
    white-space: pre-wrap;
    margin: 0;
}

#export {
    grid-column: 1 / -1;
    display: flex;
    gap: 0.5rem;
}

button {
    padding: 0.5rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 0.25rem;
    background: var(--color-surface);
    cursor: pointer;
}

button:hover {
    background: var(--color-bg);
}

#loading {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
}
```

## Deployment

### GitHub Pages

1. Enable GitHub Pages in repo settings
2. Set source to `main` branch, `/web` folder (or `/docs`)
3. Access at `https://pzfreo.github.io/wormgearcalc/`

### Build Script

Simple script to copy Python files to web folder:

```bash
#!/bin/bash
# build-web.sh

# Copy Python files
cp -r src/wormcalc web/wormcalc

# Remove CLI (not needed for web)
rm web/wormcalc/cli.py

echo "Web build complete"
```

## URL Parameters (Sharing)

Support encoding design parameters in URL for sharing:

```
https://pzfreo.github.io/wormgearcalc/?mode=envelope&worm_od=20&wheel_od=65&ratio=30
```

```javascript
function loadFromUrl() {
    const params = new URLSearchParams(window.location.search);
    if (params.has('mode')) {
        document.getElementById('mode').value = params.get('mode');
        // ... set other inputs
    }
}

function copyShareLink() {
    const params = new URLSearchParams();
    params.set('mode', document.getElementById('mode').value);
    // ... add other parameters
    
    const url = `${window.location.origin}${window.location.pathname}?${params}`;
    navigator.clipboard.writeText(url);
}
```

## Testing

### Manual Testing

1. Load page, verify Pyodide initializes
2. Change inputs, verify results update
3. Test each design mode
4. Verify validation messages display correctly
5. Test JSON copy and MD download
6. Test on mobile viewport

### Automated Testing

Consider Playwright for browser automation:

```javascript
// tests/web.spec.js
test('calculates from envelope', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('#loading', { state: 'hidden' });
    
    await page.fill('#worm-od', '20');
    await page.fill('#wheel-od', '65');
    await page.fill('#ratio', '30');
    
    await page.waitForSelector('#results-text');
    const results = await page.textContent('#results-text');
    
    expect(results).toContain('Ratio: 30:1');
    expect(results).toContain('Module:');
});
```

## Performance Considerations

### Pyodide Load Time

- First load: ~5-10 seconds (downloading WASM)
- Subsequent loads: ~1-2 seconds (cached)

Mitigations:
- Show clear loading indicator
- Consider service worker for caching

### Calculation Speed

Pure Python calculations are fast (~1ms). No optimization needed.

### Bundle Size

With zero dependencies, only loading:
- Pyodide core (~10MB, cached)
- wormcalc Python files (~30KB)

Much smaller than full NumPy/SciPy stack.
