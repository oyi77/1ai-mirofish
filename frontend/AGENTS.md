<!-- Generated: 2026-05-06 -->

# MiroFish Frontend - Vue 3 + Vite SPA

## Purpose
Vue 3 single-page application providing the user interface for MiroFish prediction engine. Implements a 5-step workflow guiding users through document upload, graph building, simulation configuration, report generation, and interactive analysis.

**Tech**: Vue 3, Vite 7, Axios, D3, Vue Router, Vue-i18n

## Quick Start

```bash
# Setup
npm install

# Dev
npm run dev              # Starts Vite on http://localhost:3000

# Build
npm run build           # Creates dist/ for production
npm run preview         # Preview production build
```

## Directory Structure

```
frontend/
├── src/
│   ├── api/                          # API client layer
│   │   ├── index.js                 # Axios instance, base config
│   │   ├── graph.js                 # Graph/project API client
│   │   ├── report.js                # Report API client
│   │   └── simulation.js            # Simulation API client
│   │
│   ├── components/                   # Reusable Vue components
│   │   ├── Step1GraphBuild.vue      # File upload & graph visualization
│   │   ├── Step2EnvSetup.vue        # Simulation setup configuration
│   │   ├── Step3Simulation.vue      # Simulation launch
│   │   ├── Step4Report.vue          # Report generation
│   │   ├── Step5Interaction.vue     # Interactive follow-ups
│   │   ├── GraphPanel.vue           # D3 graph visualization
│   │   ├── HistoryDatabase.vue      # Project history browser
│   │   └── LanguageSwitcher.vue     # Language selection (EN/ZH)
│   │
│   ├── views/                        # Page-level components
│   │   ├── Home.vue                 # Landing page
│   │   ├── MainView.vue             # Main 5-step workflow
│   │   ├── SimulationView.vue       # Simulation configuration
│   │   ├── SimulationRunView.vue    # Live simulation monitoring
│   │   ├── ReportView.vue           # Report display
│   │   ├── InteractionView.vue      # Interaction interface
│   │   └── Process.vue              # Progress tracking
│   │
│   ├── router/
│   │   └── index.js                 # Vue Router configuration
│   │
│   ├── store/
│   │   └── pendingUpload.js         # Pinia/manual state (file uploads)
│   │
│   ├── i18n/
│   │   └── index.js                 # Vue-i18n setup
│   │
│   ├── assets/
│   │   └── logo/                    # Logo images
│   │
│   ├── App.vue                      # Root component
│   ├── main.js                      # Vue app entry point
│   │
│   ├── public/                      # Static assets (copied to dist)
│   ├── index.html                   # HTML entry point
│   ├── vite.config.js               # Vite build configuration
│   ├── package.json                 # Dependencies
│   └── .env, .env.production        # Environment variables
```

## Component Hierarchy

```
App.vue
├── Home.vue
│   └── LanguageSwitcher.vue
│
├── MainView.vue (5-Step Workflow)
│   ├── Step1GraphBuild.vue
│   │   ├── GraphPanel.vue (D3 visualization)
│   │   └── File upload form
│   │
│   ├── Step2EnvSetup.vue
│   │   └── Configuration form
│   │
│   ├── Step3Simulation.vue
│   │   └── Agent selection & launch
│   │
│   ├── Step4Report.vue
│   │   └── Report display & export
│   │
│   └── Step5Interaction.vue
│       └── Follow-up questions interface
│
├── SimulationView.vue
├── SimulationRunView.vue (Live monitoring)
├── ReportView.vue
├── InteractionView.vue
├── Process.vue
└── HistoryDatabase.vue
```

## API Clients

### Usage Example

```javascript
// frontend/src/api/graph.js
import { api } from './index'

export const uploadFile = (file, projectName) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', projectName)
  return api.post('/api/graph/project/upload', formData)
}

// In component:
import { uploadFile } from '@/api/graph'

async uploadProject() {
  const result = await uploadFile(this.file, this.projectName)
  this.projectId = result.data.project_id
}
```

### Available Clients

**Graph API** (`api/graph.js`):
- `uploadFile(file, projectName)` - Create project from file
- `getProject(projectId)` - Get project details
- `listProjects(limit)` - List all projects
- `generateOntology(projectId)` - Generate ontology
- `buildGraph(projectId)` - Build knowledge graph
- `getGraphStatus(projectId)` - Check status

**Simulation API** (`api/simulation.js`):
- `createSimulation(config)` - Create simulation
- `runSimulation(simulationId)` - Execute simulation
- `getSimulationStatus(simulationId)` - Check status
- `getSimulationResults(simulationId)` - Get results
- `cancelSimulation(simulationId)` - Cancel running

**Report API** (`api/report.js`):
- `generateReport(simulationId)` - Generate report
- `getReport(reportId)` - Get report details
- `listReports(limit)` - List all reports

## Workflow: Step-by-Step

### Step 1: Graph Building
- User uploads PDF/MD/TXT file
- Backend parses and extracts entities
- D3 visualizes knowledge graph
- User reviews graph and proceeds

### Step 2: Environment Setup
- Configure simulation requirements
- Define scope and parameters
- Set chunk size for text processing

### Step 3: Simulation
- Select agent personalities (OASIS profiles)
- Configure round count
- Choose simulation platform (Twitter, Reddit, or generic)

### Step 4: Report
- Backend generates prediction report using LLM
- Display agent insights and analysis
- Show key findings and patterns

### Step 5: Interaction
- Ask follow-up questions
- Drill-down into specific predictions
- Refine analysis based on new questions

## i18n (Internationalization)

All user-facing strings use translation keys:

```vue
<template>
  <h1>{{ $t('workflow.step1.title') }}</h1>
  <p>{{ $t('workflow.step1.description') }}</p>
</template>
```

Translation files:
- `locales/en.json` - English translations
- `locales/zh.json` - Chinese translations

Add new keys:
```json
// locales/en.json
{
  "workflow": {
    "step1": {
      "title": "Upload Document",
      "description": "Upload a PDF, Markdown, or text file to build a knowledge graph"
    }
  }
}
```

## State Management

### Upload State (Pinia or manual)

```javascript
// src/store/pendingUpload.js
export const usePendingUploadStore = defineStore('pendingUpload', {
  state: () => ({
    files: [],
    currentFile: null
  }),
  actions: {
    addFile(file) {
      this.files.push(file)
    },
    setCurrentFile(file) {
      this.currentFile = file
    }
  }
})
```

## Routing

```javascript
// src/router/index.js
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/main', component: MainView },
    { path: '/simulation/:id', component: SimulationView },
    { path: '/report/:id', component: ReportView },
  ]
})
```

## Development

### Add a New Component

1. Create `src/components/MyComponent.vue`:
```vue
<template>
  <div class="my-component">
    <h2>{{ $t('myComponent.title') }}</h2>
  </div>
</template>

<script>
export default {
  name: 'MyComponent',
  props: {
    data: Object
  },
  methods: {
    async loadData() {
      // Fetch from API
    }
  }
}
</script>

<style scoped>
.my-component {
  /* Styles */
}
</style>
```

2. Import in parent:
```vue
<script>
import MyComponent from '@/components/MyComponent.vue'
</script>

<template>
  <MyComponent :data="projectData" />
</template>
```

3. Add translations:
```json
// locales/en.json
{
  "myComponent": {
    "title": "My Component Title"
  }
}
```

### Add an API Endpoint Client

1. Create `src/api/my-api.js`:
```javascript
import { api } from './index'

export const myApiCall = (param1, param2) => {
  return api.post('/api/endpoint', { param1, param2 })
}
```

2. Import in component:
```vue
<script>
import { myApiCall } from '@/api/my-api'
</script>
```

### Modify Workflow Steps

Edit `src/components/Step*.vue` and `src/views/MainView.vue`:
- Add form fields
- Call different API endpoints
- Update state and progress

## D3 Graph Visualization

`GraphPanel.vue` uses D3 for knowledge graph display:

```vue
<script>
import * as d3 from 'd3'

export default {
  props: {
    graphData: Object  // { nodes: [], edges: [] }
  },
  methods: {
    renderGraph() {
      const svg = d3.select(this.$el).append('svg')
      // D3 visualization code
    }
  }
}
</script>
```

## Environment Configuration

### Development (`.env`)
```bash
VITE_API_BASE_URL=http://localhost:5001
```

### Production (`.env.production`)
```bash
VITE_API_BASE_URL=https://api.mirofish.com
```

Access in code:
```javascript
const apiUrl = import.meta.env.VITE_API_BASE_URL
```

## Performance Optimization

1. **Code Splitting**: Vite automatically splits routes
2. **Lazy Loading**: Use dynamic imports for large components
3. **Image Optimization**: Compress logos before committing
4. **Caching**: Axios instance can cache API responses

## Testing

```bash
# Run tests (if configured)
npm run test

# Build to verify
npm run build
```

## Build & Deployment

### Development Build
```bash
npm run dev  # Hot reload
```

### Production Build
```bash
npm run build
# Creates optimized dist/ folder
```

### Deploy to CDN or Backend
```bash
# Option 1: Serve from backend
cp -r dist/* /backend/static/

# Option 2: Upload to CDN
# Upload dist/ contents to your CDN

# Update API_BASE_URL if backend moves
```

## Debugging

```bash
# Check browser console for errors
# Vue DevTools extension recommended: https://devtools.vuejs.org/

# Network tab to inspect API calls
# Storage tab to check localStorage/sessionStorage

# Chrome DevTools: F12 → Network/Console/Application tabs
```

## Dependencies

### Core
- `vue@3.5.24` - UI framework
- `vite@7.2.4` - Build tool
- `axios@1.14.0` - HTTP client
- `d3@7.9.0` - Graph visualization

### Router & i18n
- `vue-router@4.6.3` - Client-side routing
- `vue-i18n@11.3.0` - Translation system

### Build Tools
- `@vitejs/plugin-vue@6.0.1` - Vue support in Vite

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "API call fails with CORS error" | Check backend CORS config; should allow frontend origin |
| "Graph doesn't render" | Check graphData prop format; inspect D3 console errors |
| "Translation key not found" | Add key to locales/en.json and locales/zh.json |
| "File upload stuck" | Check file size < 50MB; verify backend is running |
| "Port 3000 already in use" | `sudo lsof -i :3000; kill -9 <PID>` or change VITE port |

## File Structure for New Features

When adding features, follow this structure:

```
Feature: Upload Profile Picture
├── src/api/profile.js                    # API client
├── src/components/ProfileUpload.vue      # Reusable component
├── src/views/ProfileView.vue             # Page-level view
├── locales/en.json                       # Update translations
├── locales/zh.json                       # Update translations
└── backend/app/api/profile.py            # Backend endpoint
```

## Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Axios Documentation](https://axios-http.com/)
- [D3 Documentation](https://d3js.org/)
- [Vue Router](https://router.vuejs.org/)
- [Vue-i18n](https://vue-i18n.intlify.dev/)

