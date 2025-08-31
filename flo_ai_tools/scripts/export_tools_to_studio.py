#!/usr/bin/env python3
"""
Script to export all tools from flo_ai_tools to a JSON format compatible with Flo AI Studio.

This script:
1. Inspects all tools in flo_ai_tools
2. Extracts their metadata (name, description, parameters)
3. Exports them to a JSON file that can be loaded into the studio
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the parent directory to the path so we can import flo_ai_tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from flo_ai_tools import (
    # Redshift tools
    execute_redshift_query,
    execute_batch_redshift_queries,
    get_redshift_table_schema,
    list_redshift_tables,
    get_redshift_table_info,
    test_redshift_connection,
    get_redshift_connection_info,
    # BigQuery tools
    execute_bigquery_query,
    execute_batch_bigquery_queries,
    get_bigquery_table_schema,
    list_bigquery_datasets,
    list_bigquery_tables,
    get_bigquery_table_info,
    test_bigquery_connection,
    get_bigquery_project_info,
    create_bigquery_dataset,
    delete_bigquery_dataset,
)


def extract_tool_metadata(tool_function) -> Dict[str, Any]:
    """
    Extract metadata from a tool function decorated with @flo_tool.

    Args:
        tool_function: The decorated function

    Returns:
        Dictionary containing tool metadata
    """
    if not hasattr(tool_function, 'tool'):
        return None

    tool_obj = tool_function.tool

    # Extract basic metadata
    metadata = {
        'name': tool_obj.name,
        'description': tool_obj.description,
        'category': _determine_category(tool_obj.name),
        'provider': _determine_provider(tool_obj.name),
        'parameters': {},
    }

    # Extract parameter information
    if hasattr(tool_obj, 'parameters') and tool_obj.parameters:
        for param_name, param_info in tool_obj.parameters.items():
            metadata['parameters'][param_name] = {
                'type': param_info.get('type', 'string'),
                'description': param_info.get('description', ''),
                'required': param_info.get('required', True),
                'default': param_info.get('default', None),
            }

    return metadata


def _determine_category(tool_name: str) -> str:
    """Determine the category of a tool based on its name."""
    tool_name_lower = tool_name.lower()

    if 'redshift' in tool_name_lower:
        return 'Database - Redshift'
    elif 'bigquery' in tool_name_lower:
        return 'Database - BigQuery'
    elif 'query' in tool_name_lower:
        return 'Database - Query'
    elif 'schema' in tool_name_lower:
        return 'Database - Schema'
    elif 'table' in tool_name_lower:
        return 'Database - Table'
    elif 'dataset' in tool_name_lower:
        return 'Database - Dataset'
    elif 'connection' in tool_name_lower:
        return 'Database - Connection'
    elif 'batch' in tool_name_lower:
        return 'Database - Batch Operations'
    else:
        return 'Database - General'


def _determine_provider(tool_name: str) -> str:
    """Determine the provider of a tool based on its name."""
    tool_name_lower = tool_name.lower()

    if 'redshift' in tool_name_lower:
        return 'Amazon Redshift'
    elif 'bigquery' in tool_name_lower:
        return 'Google BigQuery'
    else:
        return 'Generic Database'


def generate_studio_tools_json() -> List[Dict[str, Any]]:
    """
    Generate a list of tools in the format expected by Flo AI Studio.

    Returns:
        List of tool objects compatible with the studio
    """
    # Get all tool functions
    tool_functions = [
        # Redshift tools
        execute_redshift_query,
        execute_batch_redshift_queries,
        get_redshift_table_schema,
        list_redshift_tables,
        get_redshift_table_info,
        test_redshift_connection,
        get_redshift_connection_info,
        # BigQuery tools
        execute_bigquery_query,
        execute_batch_bigquery_queries,
        get_bigquery_table_schema,
        list_bigquery_datasets,
        list_bigquery_tables,
        get_bigquery_table_info,
        test_bigquery_connection,
        get_bigquery_project_info,
        create_bigquery_dataset,
        delete_bigquery_dataset,
    ]

    # Extract metadata from each tool
    tools = []
    for tool_func in tool_functions:
        metadata = extract_tool_metadata(tool_func)
        if metadata:
            tools.append(metadata)

    return tools


def generate_simple_studio_format(tools: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Generate a simplified format that matches the current studio implementation.

    Args:
        tools: List of detailed tool metadata

    Returns:
        List of tools in simple {name, description} format
    """
    simple_tools = []

    for tool in tools:
        # Create a descriptive name that's more user-friendly
        friendly_name = tool['name'].replace('_', ' ').title()

        # Create a comprehensive description
        description = f"{tool['description']} (Provider: {tool['provider']}, Category: {tool['category']})"

        simple_tools.append(
            {
                'name': tool['name'],  # Keep original name for YAML export
                'description': description,
                'friendly_name': friendly_name,
                'category': tool['category'],
                'provider': tool['provider'],
            }
        )

    return simple_tools


def export_tools_to_json(output_path: str = None, format_type: str = 'detailed'):
    """
    Export tools to JSON file.

    Args:
        output_path: Path to output JSON file
        format_type: 'detailed' for full metadata, 'simple' for studio-compatible format
    """
    if output_path is None:
        # Create output directory if it doesn't exist
        output_dir = Path(__file__).parent / 'exports'
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / 'flo_ai_tools_studio.json'

    # Generate tools
    if format_type == 'detailed':
        tools = generate_studio_tools_json()
        output_data = {
            'metadata': {
                'name': 'Flo AI Tools - Complete Export',
                'version': '1.0.0',
                'description': 'Complete export of all tools from flo_ai_tools package',
                'total_tools': len(tools),
                'categories': list(set(tool['category'] for tool in tools)),
                'providers': list(set(tool['provider'] for tool in tools)),
            },
            'tools': tools,
        }
    else:  # simple format
        detailed_tools = generate_studio_tools_json()
        tools = generate_simple_studio_format(detailed_tools)
        output_data = {
            'metadata': {
                'name': 'Flo AI Tools - Studio Format',
                'version': '1.0.0',
                'description': 'Tools exported in Flo AI Studio compatible format',
                'total_tools': len(tools),
            },
            'tools': tools,
        }

    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f'✅ Exported {len(tools)} tools to: {output_path}')

    # Also create a simple tools-only file for easy studio integration
    if format_type == 'simple':
        simple_output_path = Path(output_path).parent / 'flo_ai_tools_simple.json'
        simple_tools = [
            {'name': tool['name'], 'description': tool['description']} for tool in tools
        ]

        with open(simple_output_path, 'w', encoding='utf-8') as f:
            json.dump(simple_tools, f, indent=2, ensure_ascii=False)

        print(f'✅ Also created simple format: {simple_output_path}')

    return output_path


def generate_studio_integration_guide():
    """Generate a guide for integrating the exported tools into the studio."""
    guide = """
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
"""

    guide_path = Path(__file__).parent / 'exports' / 'STUDIO_INTEGRATION_GUIDE.md'
    guide_path.parent.mkdir(exist_ok=True)

    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide)

    print(f'✅ Generated integration guide: {guide_path}')


def main():
    """Main function to export tools."""
    print('🚀 Exporting Flo AI Tools for Studio Integration')
    print('=' * 60)

    try:
        # Export tools in both formats
        print('\n📦 Exporting detailed format...')
        export_tools_to_json(format_type='detailed')

        print('\n📦 Exporting studio-compatible format...')
        export_tools_to_json(format_type='simple')

        print('\n📚 Generating integration guide...')
        generate_studio_integration_guide()

        print('\n✅ Export completed successfully!')
        print("\n📁 Check the 'exports' directory for:")
        print('   - flo_ai_tools_studio.json (detailed format)')
        print('   - flo_ai_tools_simple.json (studio-compatible)')
        print('   - STUDIO_INTEGRATION_GUIDE.md (integration instructions)')

    except Exception as e:
        print(f'\n❌ Export failed: {str(e)}')
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
