
# Flo AI Studio Integration Guide

## How to Use the Exported Tools

### Option 1: Replace Default Tools (Recommended)
1. Copy the contents of `flo_ai_tools_simple.json`
2. In `studio/src/store/designerStore.ts`, replace the `availableTools` array:

```typescript
const defaultConfig: DesignerConfig = {
  availableTools: [
    // Paste the exported tools here
    // They will automatically appear in the studio sidebar
  ],
  // ... rest of config
};
```

### Option 2: Load Tools Dynamically
1. Add a function to load tools from JSON:

```typescript
// In designerStore.ts
loadToolsFromJSON: (toolsJson: string) => {
  try {
    const tools = JSON.parse(toolsJson);
    set((state) => ({
      config: {
        ...state.config,
        availableTools: tools
      }
    }));
  } catch (error) {
    console.error('Failed to load tools:', error);
  }
}
```

2. Use it to load the exported tools:

```typescript
const { loadToolsFromJSON } = useDesignerStore();

// Load tools from file or API
fetch('/tools/flo_ai_tools_simple.json')
  .then(response => response.text())
  .then(jsonContent => loadToolsFromJSON(jsonContent));
```

### Option 3: Import via YAML
1. Create a workflow YAML that includes the tools
2. Import the YAML into the studio
3. Tools will be automatically available

## Tool Categories
- **Database - Redshift**: Amazon Redshift database operations
- **Database - BigQuery**: Google BigQuery database operations
- **Database - Query**: General database query execution
- **Database - Schema**: Table and dataset schema operations
- **Database - Table**: Table management operations
- **Database - Dataset**: Dataset management operations
- **Database - Connection**: Connection testing and management
- **Database - Batch Operations**: Batch query execution

## Available Providers
- Amazon Redshift
- Google BigQuery
- Generic Database

## Notes
- All tools are async and use the @flo_tool decorator
- Tools automatically handle connection management
- Environment variables are used for configuration
- Tools are designed to work with AI agents
- **This export was generated automatically** - no manual updates required!
