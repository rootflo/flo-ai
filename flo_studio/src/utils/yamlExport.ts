import { dump } from 'js-yaml';
import { Agent, AriumWorkflow } from '@/types/agent';
import { CustomNode, CustomEdge } from '@/types/reactflow';

export interface ExportData {
  nodes: CustomNode[];
  edges: CustomEdge[];
  workflowName: string;
  workflowDescription: string;
  workflowVersion: string;
}

export function generateAriumYAML(data: ExportData): string {
  const { nodes, edges, workflowName, workflowDescription, workflowVersion } = data;

  // Extract agents, tools, and routers
  const agents: Agent[] = [];
  const tools: string[] = [];
  const routers: any[] = [];
  
  nodes.forEach((node) => {
    if (node.type === 'agent') {
      const agentData = node.data as any;
      agents.push(agentData.agent);
    } else if (node.type === 'tool') {
      const toolData = node.data as any;
      tools.push(toolData.tool.name);
    } else if (node.type === 'router') {
      const routerData = node.data as any;
      routers.push(routerData.router);
    }
  });

  // Determine start and end nodes
  const nodeConnections = new Map<string, { incoming: string[], outgoing: string[] }>();
  
  // Initialize connections map
  nodes.forEach((node) => {
    nodeConnections.set(node.id, { incoming: [], outgoing: [] });
  });

  // Build connections
  edges.forEach((edge) => {
    const sourceConnections = nodeConnections.get(edge.source);
    const targetConnections = nodeConnections.get(edge.target);
    
    if (sourceConnections) {
      sourceConnections.outgoing.push(edge.target);
    }
    if (targetConnections) {
      targetConnections.incoming.push(edge.source);
    }
  });

  // Find start nodes (nodes with no incoming connections)
  const startNodes = nodes.filter((node) => {
    const connections = nodeConnections.get(node.id);
    return connections && connections.incoming.length === 0;
  });

  // Find end nodes (nodes with no outgoing connections)
  const endNodes = nodes.filter((node) => {
    const connections = nodeConnections.get(node.id);
    return connections && connections.outgoing.length === 0;
  });

  // Build workflow edges - now routers are nodes, not edge properties
  const workflowEdges: Array<{
    from: string;
    to: string[];
    router?: string;
  }> = [];

  // Group edges by source
  const edgesBySource = new Map<string, CustomEdge[]>();
  edges.forEach((edge) => {
    if (!edgesBySource.has(edge.source)) {
      edgesBySource.set(edge.source, []);
    }
    edgesBySource.get(edge.source)!.push(edge);
  });

  // Create workflow edges - check if target is a router
  edgesBySource.forEach((sourceEdges, sourceId) => {
    const targets = sourceEdges.map((edge) => edge.target);
    
    // Check if any target is a router node
    const routerTarget = targets.find(targetId => {
      const targetNode = nodes.find(n => n.id === targetId);
      return targetNode?.type === 'router';
    });

    if (routerTarget) {
      // If connecting to a router, use the router's name
      const routerNode = nodes.find(n => n.id === routerTarget);
      const routerData = routerNode?.data as any;
      workflowEdges.push({
        from: sourceId,
        to: targets.filter(t => t !== routerTarget), // Exclude router from direct targets
        router: routerData?.router?.name,
      });
    } else {
      // Direct connection without router
      workflowEdges.push({
        from: sourceId,
        to: targets,
      });
    }
  });

  // Convert agents to YAML format
  const yamlAgents = agents.map((agent) => {
    const yamlAgent: any = {
      name: agent.name,
      role: agent.role,
      job: agent.job,
      model: {
        provider: agent.model.provider,
        name: agent.model.name,
      },
    };

    // Add base_url if present
    if (agent.model.base_url) {
      yamlAgent.model.base_url = agent.model.base_url;
    }

    // Add settings if present
    if (agent.settings) {
      yamlAgent.settings = {};
      if (agent.settings.temperature !== undefined) {
        yamlAgent.settings.temperature = agent.settings.temperature;
      }
      if (agent.settings.max_retries !== undefined) {
        yamlAgent.settings.max_retries = agent.settings.max_retries;
      }
      if (agent.settings.reasoning_pattern !== undefined) {
        yamlAgent.settings.reasoning_pattern = agent.settings.reasoning_pattern;
      }
    }

    // Add tools if present
    if (agent.tools && agent.tools.length > 0) {
      yamlAgent.tools = agent.tools;
    }

    // Add parser if present
    if (agent.parser && agent.parser.fields && agent.parser.fields.length > 0) {
      yamlAgent.parser = {
        name: agent.parser.name,
        version: agent.parser.version || '1.0.0',
        description: agent.parser.description,
        fields: agent.parser.fields.map((field) => ({
          name: field.name,
          type: field.type,
          description: field.description,
          required: field.required,
          values: field.values,
          items: field.items,
        })),
      };
    }

    return yamlAgent;
  });

  // Convert routers to YAML format
  const yamlRouters = routers.map((router) => {
    const yamlRouter: any = {
      name: router.name,
      type: router.type || 'smart',
    };

    if (router.routing_options && Object.keys(router.routing_options).length > 0) {
      yamlRouter.routing_options = router.routing_options;
    }

    if (router.model) {
      yamlRouter.model = {
        provider: router.model.provider,
        name: router.model.name,
      };
    }

    if (router.settings) {
      yamlRouter.settings = {};
      if (router.settings.temperature !== undefined) {
        yamlRouter.settings.temperature = router.settings.temperature;
      }
      if (router.settings.fallback_strategy !== undefined) {
        yamlRouter.settings.fallback_strategy = router.settings.fallback_strategy;
      }
      if (router.settings.analysis_depth !== undefined) {
        yamlRouter.settings.analysis_depth = router.settings.analysis_depth;
      }
    }

    return yamlRouter;
  });

  // Build the final YAML structure
  const yamlStructure: any = {
    metadata: {
      name: workflowName || 'Flo AI Workflow',
      version: workflowVersion || '1.0.0',
      description: workflowDescription || 'Generated with Flo AI Studio',
      tags: ['flo-ai', 'studio-generated'],
    },
    arium: {
      agents: yamlAgents,
      tools: tools.length > 0 ? tools.map(name => ({ name })) : undefined,
      routers: yamlRouters.length > 0 ? yamlRouters : undefined,
      workflow: {
        start: startNodes.length > 0 ? startNodes[0].id : agents[0]?.id || '',
        edges: workflowEdges.filter(edge => edge.to.length > 0),
        end: endNodes.map((node) => node.id),
      },
    },
  };

  // Remove undefined fields
  const cleanYamlStructure = JSON.parse(JSON.stringify(yamlStructure, (key, value) => {
    return value === undefined ? null : value;
  }));

  // Remove null values
  function removeNulls(obj: any): any {
    if (Array.isArray(obj)) {
      return obj.map(removeNulls).filter(item => item !== null);
    } else if (obj !== null && typeof obj === 'object') {
      const cleaned: any = {};
      for (const [key, value] of Object.entries(obj)) {
        const cleanValue = removeNulls(value);
        if (cleanValue !== null && cleanValue !== undefined) {
          cleaned[key] = cleanValue;
        }
      }
      return cleaned;
    }
    return obj;
  }

  const finalStructure = removeNulls(cleanYamlStructure);

  return dump(finalStructure, {
    indent: 2,
    lineWidth: 100,
    noRefs: true,
    sortKeys: false,
  });
}

export function downloadYAML(content: string, filename: string = 'flo-ai-workflow.yaml'): void {
  const blob = new Blob([content], { type: 'text/yaml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

export function copyToClipboard(content: string): Promise<void> {
  return navigator.clipboard.writeText(content);
}
