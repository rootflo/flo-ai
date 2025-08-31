# Exporting Tools for Flo AI Studio

This document explains how to export all tools from `flo_ai_tools` to a format compatible with the Flo AI Studio.

## 🚀 Quick Export (Recommended)

### From flo_ai_tools directory:
```bash
cd flo_ai_tools
source ../.venv/bin/activate  # or your virtual environment
python export_tools.py
```

### From anywhere (auto-detects package):
```bash
python export_tools_anywhere.py [optional_path_to_flo_ai_tools]
```

## ✨ Key Features

- **🔄 Fully Automatic**: No manual updates required when adding new tools
- **📖 Dynamic Discovery**: Reads `__init__.py` to find all exported tools
- **🔍 Smart Filtering**: Automatically identifies tools vs. connection managers
- **📊 Rich Metadata**: Extracts descriptions, parameters, categories, and providers
- **🎯 Studio Ready**: Generates JSON in the exact format expected by Flo AI Studio

## 🔧 How It Works

1. **Parses `__init__.py`**: Uses AST parsing to extract all names from `__all__`
2. **Filters Tools**: Automatically excludes connection managers and non-tool items
3. **Dynamic Import**: Imports each tool function and extracts metadata
4. **Metadata Extraction**: Gets name, description, parameters, and decorates with category/provider info
5. **JSON Export**: Creates both detailed and studio-compatible formats

## 📁 What Gets Exported

The script exports all available tools in two formats:

### 1. Detailed Format (`flo_ai_tools_studio.json`)
Contains comprehensive tool metadata including:
- Tool name and description
- Parameter information (types, descriptions, required/optional)
- Category classification
- Provider information
- Full metadata for advanced use cases

### 2. Studio-Compatible Format (`flo_ai_tools_simple.json`)
Contains tools in the exact format expected by Flo AI Studio:
- Tool name
- Enhanced description with category and provider info
- Ready to paste into the studio's `availableTools` array

## 🆕 Adding New Tools

**No changes to the export script required!** Simply:

1. Add your new tool to the appropriate tools file
2. Decorate it with `@flo_tool`
3. Add it to `__init__.py` in the `__all__` list
4. Run the export script again

The script will automatically discover and export the new tool with all its metadata.

## 📊 Available Tools

### Redshift Tools (7)
- `execute_redshift_query` - Execute SQL queries on Redshift
- `execute_batch_redshift_queries` - Execute multiple queries in batch
- `get_redshift_table_schema` - Get table schema information
- `list_redshift_tables` - List all tables in a schema
- `get_redshift_table_info` - Get comprehensive table information
- `test_redshift_connection` - Test database connection
- `get_redshift_connection_info` - Get connection configuration

### BigQuery Tools (10)
- `execute_bigquery_query` - Execute SQL queries on BigQuery
- `execute_batch_bigquery_queries` - Execute multiple queries in batch
- `get_bigquery_table_schema` - Get table schema information
- `list_bigquery_datasets` - List all datasets in a project
- `list_bigquery_tables` - List all tables in a dataset
- `get_bigquery_table_info` - Get comprehensive table information
- `test_bigquery_connection` - Test database connection
- `get_bigquery_project_info` - Get project information
- `create_bigquery_dataset` - Create a new dataset
- `delete_bigquery_dataset` - Delete a dataset

## 🔗 Integration with Flo AI Studio

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
Add a function to load tools from JSON in the studio store:

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

## 🏷️ Tool Categories

Tools are automatically categorized based on their functionality:

- **Database - Redshift**: Amazon Redshift database operations
- **Database - BigQuery**: Google BigQuery database operations
- **Database - Query**: General database query execution
- **Database - Schema**: Table and dataset schema operations
- **Database - Table**: Table management operations
- **Database - Dataset**: Dataset management operations
- **Database - Connection**: Connection testing and management
- **Database - Batch Operations**: Batch query execution

## 🌐 Provider Information

Each tool includes provider information:

- **Amazon Redshift**: For Redshift-specific tools
- **Google BigQuery**: For BigQuery-specific tools
- **Generic Database**: For general database tools

## 📂 Output Files

After running the export script, you'll find these files:

### From flo_ai_tools directory:
- `scripts/exports/flo_ai_tools_studio.json` - Complete tool metadata
- `scripts/exports/flo_ai_tools_simple.json` - Studio-compatible format
- `scripts/exports/STUDIO_INTEGRATION_GUIDE.md` - Detailed integration instructions

### From anywhere:
- `flo_ai_tools_exports/flo_ai_tools_studio.json` - Complete tool metadata
- `flo_ai_tools_exports/flo_ai_tools_simple.json` - Studio-compatible format
- `flo_ai_tools_exports/STUDIO_INTEGRATION_GUIDE.md` - Integration instructions

## 🛠️ Customization

You can modify the export script to:

- Add new tool categories and providers
- Change the output format
- Add additional metadata fields
- Customize the filtering logic

## 📋 Requirements

- Python 3.8+
- All dependencies from `flo_ai_tools` package
- Access to the tool functions (they must be importable)

## 🔍 Troubleshooting

### Import Errors
If you get import errors, ensure you're running from the correct directory and that all dependencies are installed.

### Missing Tools
If some tools are missing from the export, check that they:
- Are properly decorated with `@flo_tool`
- Are imported in the `__init__.py` file
- Are included in the `__all__` list

### Studio Integration Issues
- Ensure the JSON format matches exactly what the studio expects
- Check that tool names are unique
- Verify that descriptions are properly formatted

## 🆘 Support

For issues with the export process or studio integration, check:
1. The generated integration guide
2. The studio's tool loading mechanism
3. The exported JSON format for any syntax errors
4. That all tools are properly decorated and exported

## 🎯 Benefits of Dynamic Export

- **Zero Maintenance**: Add tools without touching export scripts
- **Always Up-to-Date**: Automatically reflects current package state
- **Error Prevention**: No risk of forgetting to update export lists
- **Scalable**: Works with any number of tools
- **Consistent**: All tools get the same metadata treatment
