import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Bot, Wrench, Search, Plus } from 'lucide-react';
import { useDesignerStore } from '@/store/designerStore';
import { Agent, Tool } from '@/types/agent';

const Sidebar: React.FC = () => {
  const { config, addAgent, addTool, openAgentEditor } = useDesignerStore();
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTools = config.availableTools.filter((tool) =>
    tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tool.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleAddAgent = () => {
    openAgentEditor();
  };

  const handleAddTool = (tool: Tool) => {
    const position = {
      x: Math.random() * 400 + 100,
      y: Math.random() * 400 + 100,
    };
    addTool(tool, position);
  };

  const createQuickAgent = (template: string) => {
    const templates = {
      analyzer: {
        name: 'Content Analyzer',
        role: 'Content Analyst',
        job: 'Analyze content and extract key insights, themes, and important information.',
        model: { provider: 'openai' as const, name: 'gpt-4o-mini' },
      },
      summarizer: {
        name: 'Summarizer',
        role: 'Summary Generator',
        job: 'Create concise, actionable summaries from analysis and content.',
        model: { provider: 'openai' as const, name: 'gpt-4o-mini' },
      },
      classifier: {
        name: 'Classifier',
        role: 'Content Classifier',
        job: 'Classify content into predefined categories and route accordingly.',
        model: { provider: 'anthropic' as const, name: 'claude-3-5-sonnet-20240620' },
      },
      researcher: {
        name: 'Researcher',
        role: 'Research Specialist',
        job: 'Research topics and gather comprehensive information using available tools.',
        model: { provider: 'openai' as const, name: 'gpt-4o' },
        tools: ['web_search'],
      },
    };

    const template_config = templates[template as keyof typeof templates];
    if (template_config) {
      const agent: Agent = {
        id: `agent_${Date.now()}`,
        ...template_config,
      };

      const position = {
        x: Math.random() * 400 + 100,
        y: Math.random() * 400 + 100,
      };

      addAgent(agent, position);
    }
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
      <div className="p-4 space-y-6">
        {/* Quick Start */}
        <div>
          <h3 className="font-medium text-sm text-gray-700 mb-3">Quick Start</h3>
          <div className="text-sm text-gray-600 mb-4">
            Welcome to Flo AI Studio! Create agents and connect them to build powerful AI workflows.
          </div>
          <Button
            onClick={handleAddAgent}
            className="w-full mb-4"
            variant="outline"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Custom Agent
          </Button>
        </div>

        {/* Quick Templates */}
        <div>
          <h3 className="font-medium text-sm text-gray-700 mb-3">Agent Templates</h3>
          <div className="space-y-2">
            {[
              { key: 'analyzer', name: 'Content Analyzer', desc: 'Analyze and extract insights' },
              { key: 'summarizer', name: 'Summarizer', desc: 'Create concise summaries' },
              { key: 'classifier', name: 'Classifier', desc: 'Classify and route content' },
              { key: 'researcher', name: 'Researcher', desc: 'Research with tools' },
            ].map((template) => (
              <div
                key={template.key}
                className="p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => createQuickAgent(template.key)}
              >
                <div className="flex items-center mb-1">
                  <Bot className="w-4 h-4 text-blue-600 mr-2" />
                  <span className="font-medium text-sm">{template.name}</span>
                </div>
                <p className="text-xs text-gray-600">{template.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Available Tools */}
        <div>
          <h3 className="font-medium text-sm text-gray-700 mb-3">Available Tools</h3>
          <div className="relative mb-3">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search tools..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {filteredTools.map((tool) => (
              <div
                key={tool.name}
                className="p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleAddTool(tool)}
              >
                <div className="flex items-center mb-1">
                  <Wrench className="w-4 h-4 text-orange-600 mr-2" />
                  <span className="font-medium text-sm">{tool.name}</span>
                </div>
                <p className="text-xs text-gray-600 line-clamp-2">{tool.description}</p>
              </div>
            ))}
          </div>

          {filteredTools.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Wrench className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No tools found</p>
            </div>
          )}
        </div>

        {/* Getting Started */}
        <div className="border rounded-lg p-4 bg-blue-50">
          <h4 className="font-medium text-sm mb-2 text-blue-800">Getting Started</h4>
          <ol className="text-sm text-blue-700 space-y-1">
            <li>1. Create agents using templates or custom forms</li>
            <li>2. Add tools to enhance agent capabilities</li>
            <li>3. Connect agents by dragging from output to input</li>
            <li>4. Export as YAML when ready</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
