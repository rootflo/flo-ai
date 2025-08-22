import React, { useState } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { useDesignerStore } from '@/store/designerStore';
import { Button } from '@/components/ui/button';
import { Plus, Settings, FileText, Route } from 'lucide-react';
import FlowCanvas from '@/components/flow/FlowCanvas';
import Sidebar from '@/components/sidebar/Sidebar';
import AgentEditor from '@/components/editors/AgentEditor';
import RouterEditor from '@/components/editors/RouterEditor';
import EdgeEditor from '@/components/editors/EdgeEditor';
import YamlPreviewDrawer from '@/components/drawer/YamlPreviewDrawer';
import './App.css';

// Simplified Config Editor Modal
const ConfigEditorModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h2 className="text-lg font-semibold mb-4">Configuration</h2>
        <p className="text-sm text-gray-600 mb-4">
          Configuration editor coming soon! For now, tools and LLMs are pre-configured.
        </p>
        <Button onClick={onClose}>Close</Button>
      </div>
    </div>
  );
};

const ToolbarComponent: React.FC = () => {
  const { openAgentEditor, openRouterEditor, nodes } = useDesignerStore();
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isYamlOpen, setIsYamlOpen] = useState(false);

  return (
    <>
      <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-semibold text-gray-800">Flo AI Studio</h1>
          <div className="text-sm text-gray-600">Visual Workflow Designer</div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={openAgentEditor}>
            <Plus className="w-4 h-4 mr-1" />
            Agent
          </Button>
          <Button variant="outline" size="sm" onClick={openRouterEditor}>
            <Route className="w-4 h-4 mr-1" />
            Router
          </Button>
          <Button variant="outline" size="sm" onClick={() => setIsConfigOpen(true)}>
            <Settings className="w-4 h-4 mr-1" />
            Config
          </Button>
          {nodes.length > 0 && (
            <Button variant="outline" size="sm" onClick={() => setIsYamlOpen(true)}>
              <FileText className="w-4 h-4 mr-1" />
              Export
            </Button>
          )}
        </div>
      </div>
      <ConfigEditorModal isOpen={isConfigOpen} onClose={() => setIsConfigOpen(false)} />
    </>
  );
};

function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-100">
      <ToolbarComponent />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div className="flex-1 relative">
          <ReactFlowProvider>
            <FlowCanvas />
          </ReactFlowProvider>
        </div>
      </div>
      
      {/* Modals */}
      <AgentEditor />
      <RouterEditor />
      <EdgeEditor />
      
      {/* YAML Preview Drawer */}
      <YamlPreviewDrawer />
    </div>
  );
}

export default App;