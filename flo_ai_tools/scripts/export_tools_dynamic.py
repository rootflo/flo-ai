#!/usr/bin/env python3
"""
Dynamic script to export all tools from flo_ai_tools to JSON format for Flo AI Studio.

This script automatically:
1. Reads the __init__.py file to discover all exported tools
2. Dynamically imports and inspects each tool
3. Extracts metadata without requiring manual updates
4. Exports to JSON format compatible with the studio
5. Outputs directly to the studio folder for dynamic loading
"""

import json
import importlib
import ast
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


def parse_init_file(init_file_path: str) -> List[str]:
    """
    Parse the __init__.py file to extract all exported tool names from __all__.

    Args:
        init_file_path: Path to the __init__.py file

    Returns:
        List of tool names from __all__
    """
    with open(init_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse the Python code
    tree = ast.parse(content)

    # Find the __all__ list
    tool_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, ast.List):
                        for item in node.value.elts:
                            if isinstance(item, ast.Constant):
                                tool_names.append(item.value)

    return tool_names


def filter_tools_from_all(all_names: List[str]) -> List[str]:
    """
    Filter out non-tool items from __all__ (like connection managers).

    Args:
        all_names: List of all names from __all__

    Returns:
        List of tool names only
    """
    # Filter out connection managers and other non-tool items
    tool_names = []
    for name in all_names:
        # Skip connection managers
        if 'ConnectionManager' in name:
            continue
        # Include everything else as potential tools
        tool_names.append(name)

    return tool_names


def dynamically_import_tools(
    package_name: str, tool_names: List[str]
) -> Dict[str, Any]:
    """
    Dynamically import tools and extract their metadata.

    Args:
        package_name: Name of the package to import from
        tool_names: List of tool names to import

    Returns:
        Dictionary mapping tool names to their functions
    """
    tools = {}

    try:
        # Import the package
        package = importlib.import_module(package_name)

        for tool_name in tool_names:
            try:
                # Get the tool function from the package
                tool_func = getattr(package, tool_name)

                # Check if it has the .tool attribute (indicating it's decorated with @flo_tool)
                if hasattr(tool_func, 'tool'):
                    tools[tool_name] = tool_func
                else:
                    print(
                        f"⚠️  Warning: {tool_name} doesn't appear to be a decorated tool"
                    )

            except AttributeError as e:
                print(f'⚠️  Warning: Could not import {tool_name}: {e}')
                continue

    except ImportError as e:
        print(f'❌ Error importing package {package_name}: {e}')
        return {}

    return tools


def extract_tool_metadata(tool_function) -> Optional[Dict[str, Any]]:
    """
    Extract metadata from a tool function decorated with @flo_tool.

    Args:
        tool_function: The decorated function

    Returns:
        Dictionary containing tool metadata or None if invalid
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


def generate_studio_tools_json(tools_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate a list of tools in the format expected by Flo AI Studio.

    Args:
        tools_dict: Dictionary of tool functions

    Returns:
        List of tool objects compatible with the studio
    """
    tools = []

    for tool_name, tool_func in tools_dict.items():
        metadata = extract_tool_metadata(tool_func)
        if metadata:
            tools.append(metadata)
        else:
            print(f'⚠️  Warning: Could not extract metadata from {tool_name}')

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
        # Create a comprehensive description
        description = f"{tool['description']} (Provider: {tool['provider']}, Category: {tool['category']})"

        simple_tools.append(
            {
                'name': tool['name'],
                'description': description,
                'friendly_name': tool['name'].replace('_', ' ').title(),
                'category': tool['category'],
                'provider': tool['provider'],
            }
        )

    return simple_tools


def find_studio_directory() -> Optional[Path]:
    """
    Find the studio directory relative to the current location.

    Returns:
        Path to the studio directory or None if not found
    """
    # Start from the current script location and look for studio directory
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent.parent  # Go up to the root of the project

    studio_path = root_dir / 'studio'
    if studio_path.exists() and (studio_path / 'src').exists():
        return studio_path

    return None


def export_tools_to_json(
    package_path: str, output_path: str = None, format_type: str = 'detailed'
):
    """
    Export tools to JSON file by dynamically reading the package.

    Args:
        package_path: Path to the package directory
        output_path: Path to output JSON file
        format_type: 'detailed' for full metadata, 'simple' for studio-compatible format
    """
    # Find studio directory for output
    studio_dir = find_studio_directory()
    if not studio_dir:
        print('⚠️  Studio directory not found, using local exports directory')
        if output_path is None:
            output_dir = Path(__file__).parent / 'exports'
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / 'flo_ai_tools_studio.json'
    else:
        # Create tools directory in studio
        tools_dir = studio_dir / 'public' / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        if output_path is None:
            output_path = tools_dir / 'flo_ai_tools_studio.json'

    # Parse the __init__.py file
    init_file = Path(package_path) / '__init__.py'
    if not init_file.exists():
        raise FileNotFoundError(f'__init__.py not found at {init_file}')

    print(f'📖 Reading {init_file}...')
    all_names = parse_init_file(str(init_file))
    print(f'📋 Found {len(all_names)} items in __all__')

    # Filter to get only tool names
    tool_names = filter_tools_from_all(all_names)
    print(f'🔧 Identified {len(tool_names)} potential tools')

    # Dynamically import the tools
    package_name = Path(package_path).name
    print(f'📦 Importing tools from {package_name}...')
    tools_dict = dynamically_import_tools(package_name, tool_names)
    print(f'✅ Successfully imported {len(tools_dict)} tools')

    # Generate tools metadata
    if format_type == 'detailed':
        tools = generate_studio_tools_json(tools_dict)
        output_data = {
            'metadata': {
                'name': 'Flo AI Tools - Complete Export',
                'version': '1.0.0',
                'description': 'Complete export of all tools from flo_ai_tools package',
                'total_tools': len(tools),
                'categories': list(set(tool['category'] for tool in tools)),
                'providers': list(set(tool['provider'] for tool in tools)),
                'source': f'Dynamically extracted from {package_name}/__init__.py',
            },
            'tools': tools,
        }
    else:  # simple format
        detailed_tools = generate_studio_tools_json(tools_dict)
        tools = generate_simple_studio_format(detailed_tools)
        output_data = {
            'metadata': {
                'name': 'Flo AI Tools - Studio Format',
                'version': '1.0.0',
                'description': 'Tools exported in Flo AI Studio compatible format',
                'total_tools': len(tools),
                'source': f'Dynamically extracted from {package_name}/__init__.py',
            },
            'tools': tools,
        }

    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f'✅ Exported {len(tools)} tools to: {output_path}')

    # Also create a simple tools-only file for easy studio integration
    if format_type == 'simple':
        simple_output_path = output_path.parent / 'flo_ai_tools_simple.json'
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

### Option 1: Dynamic Loading (Recommended)
The tools are now automatically exported to `studio/public/tools/` and can be loaded dynamically:

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

### Option 2: Replace Default Tools
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
- Tools are now exported directly to `studio/public/tools/` for dynamic loading
"""

    # Try to save to studio directory, fallback to local
    studio_dir = find_studio_directory()
    if studio_dir:
        guide_path = studio_dir / 'docs' / 'STUDIO_INTEGRATION_GUIDE.md'
        guide_path.parent.mkdir(exist_ok=True)
    else:
        guide_path = Path(__file__).parent / 'exports' / 'STUDIO_INTEGRATION_GUIDE.md'
        guide_path.parent.mkdir(exist_ok=True)

    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide)

    print(f'✅ Generated integration guide: {guide_path}')


def main():
    """Main function to export tools dynamically."""
    print('🚀 Dynamically Exporting Flo AI Tools for Studio Integration')
    print('=' * 70)

    try:
        # Get the package path (assuming we're running from flo_ai_tools root)
        package_path = Path(__file__).parent.parent / 'flo_ai_tools'

        if not package_path.exists():
            print(f'❌ Package directory not found: {package_path}')
            print('Please run this script from the flo_ai_tools root directory')
            sys.exit(1)

        print(f'📁 Package path: {package_path}')

        # Check if studio directory exists
        studio_dir = find_studio_directory()
        if studio_dir:
            print(f'🎨 Studio directory found: {studio_dir}')
            print('📁 Tools will be exported to studio/public/tools/')
        else:
            print('⚠️  Studio directory not found, using local exports')

        # Export tools in both formats
        print('\n📦 Exporting detailed format...')
        export_tools_to_json(str(package_path), format_type='detailed')

        print('\n📦 Exporting studio-compatible format...')
        export_tools_to_json(str(package_path), format_type='simple')

        print('\n📚 Generating integration guide...')
        generate_studio_integration_guide()

        print('\n✅ Export completed successfully!')

        if studio_dir:
            print(f'\n📁 Tools exported to: {studio_dir}/public/tools/')
            print('   - flo_ai_tools_studio.json (detailed format)')
            print('   - flo_ai_tools_simple.json (studio-compatible)')
            print(
                '\n📚 Integration guide: {studio_dir}/docs/STUDIO_INTEGRATION_GUIDE.md'
            )
        else:
            print("\n📁 Check the 'scripts/exports' directory for:")
            print('   - flo_ai_tools_studio.json (detailed format)')
            print('   - flo_ai_tools_simple.json (studio-compatible)')
            print('   - STUDIO_INTEGRATION_GUIDE.md (integration instructions)')

        print(
            '\n🔄 **No manual updates required!** The script automatically discovers all tools.'
        )

    except Exception as e:
        print(f'\n❌ Export failed: {str(e)}')
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
