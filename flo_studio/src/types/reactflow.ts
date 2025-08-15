import { Node, Edge } from 'reactflow';
import { Agent, Tool } from './agent';

export interface AgentNodeData {
  agent: Agent;
  isStart?: boolean;
  isEnd?: boolean;
}

export interface ToolNodeData {
  tool: Tool;
  isEnd?: boolean;
}

export type CustomNode = Node<AgentNodeData | ToolNodeData>;

export interface CustomEdgeData {
  router?: string;
  label?: string;
}

export type CustomEdge = Edge<CustomEdgeData>;

export type NodeType = 'agent' | 'tool';

export interface FlowState {
  nodes: CustomNode[];
  edges: CustomEdge[];
  selectedNode?: CustomNode;
  selectedEdge?: CustomEdge;
}
