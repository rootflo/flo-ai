import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useDesignerStore } from '@/store/designerStore';
import { Router } from '@/types/agent';

const RouterEditor: React.FC = () => {
  const {
    isRouterEditorOpen,
    closeRouterEditor,
    selectedNode,
    updateRouter,
    addRouter,
    config,
  } = useDesignerStore();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'smart' as const,
    provider: 'openai' as const,
    modelName: 'gpt-4o-mini',
    temperature: 0.3,
    fallbackStrategy: 'first' as const,
    routingOptions: {} as Record<string, string>,
  });

  const [routingOptionKey, setRoutingOptionKey] = useState('');
  const [routingOptionValue, setRoutingOptionValue] = useState('');
  const [isNewRouter, setIsNewRouter] = useState(false);

  useEffect(() => {
    if (selectedNode && selectedNode.type === 'router') {
      const routerData = selectedNode.data as any;
      const router = routerData.router;
      setIsNewRouter(false);
      
      setFormData({
        name: router.name || '',
        description: router.description || '',
        type: router.type || 'smart',
        provider: router.model?.provider || 'openai',
        modelName: router.model?.name || 'gpt-4o-mini',
        temperature: router.settings?.temperature || 0.3,
        fallbackStrategy: router.settings?.fallback_strategy || 'first',
        routingOptions: router.routing_options || {},
      });
    } else if (isRouterEditorOpen) {
      setIsNewRouter(true);
      setFormData({
        name: '',
        description: '',
        type: 'smart',
        provider: 'openai',
        modelName: 'gpt-4o-mini',
        temperature: 0.3,
        fallbackStrategy: 'first',
        routingOptions: {},
      });
    }
  }, [selectedNode, isRouterEditorOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const router: Router = {
      id: isNewRouter ? `router_${Date.now()}` : selectedNode!.id,
      name: formData.name,
      description: formData.description,
      type: formData.type,
      model: {
        provider: formData.provider,
        name: formData.modelName,
      },
      settings: {
        temperature: formData.temperature,
        fallback_strategy: formData.fallbackStrategy,
      },
      routing_options: formData.routingOptions,
    };

    if (isNewRouter) {
      addRouter(router, { x: 100, y: 100 });
    } else {
      updateRouter(router.id!, router);
    }

    closeRouterEditor();
  };

  const addRoutingOption = () => {
    if (routingOptionKey && routingOptionValue) {
      setFormData(prev => ({
        ...prev,
        routingOptions: {
          ...prev.routingOptions,
          [routingOptionKey]: routingOptionValue,
        },
      }));
      setRoutingOptionKey('');
      setRoutingOptionValue('');
    }
  };

  const removeRoutingOption = (key: string) => {
    setFormData(prev => {
      const newOptions = { ...prev.routingOptions };
      delete newOptions[key];
      return { ...prev, routingOptions: newOptions };
    });
  };

  const availableModels = config.availableLLMs.filter(
    (llm) => llm.provider === formData.provider
  );

  return (
    <Dialog open={isRouterEditorOpen} onOpenChange={closeRouterEditor}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isNewRouter ? 'Create New Router' : 'Edit Router'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Router Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Content Router"
                required
              />
            </div>
            <div>
              <Label>Router Type</Label>
              <Select
                value={formData.type}
                onValueChange={(value) => setFormData(prev => ({ ...prev, type: value as any }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="smart">Smart Router</SelectItem>
                  <SelectItem value="task_classifier">Task Classifier</SelectItem>
                  <SelectItem value="conversation_analysis">Conversation Analysis</SelectItem>
                  <SelectItem value="custom">Custom Router</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Describe how this router works..."
              rows={3}
              required
            />
          </div>

          {formData.type !== 'custom' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>LLM Provider</Label>
                  <Select
                    value={formData.provider}
                    onValueChange={(value) => {
                      setFormData(prev => ({ 
                        ...prev, 
                        provider: value as any,
                        modelName: config.availableLLMs.find(llm => llm.provider === value)?.name || ''
                      }));
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                      <SelectItem value="gemini">Google Gemini</SelectItem>
                      <SelectItem value="ollama">Ollama</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Model</Label>
                  <Select
                    value={formData.modelName}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, modelName: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {availableModels.map((model) => (
                        <SelectItem key={model.name} value={model.name}>
                          {model.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Temperature</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={formData.temperature}
                    onChange={(e) => setFormData(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                  />
                </div>
                <div>
                  <Label>Fallback Strategy</Label>
                  <Select
                    value={formData.fallbackStrategy}
                    onValueChange={(value) => setFormData(prev => ({ ...prev, fallbackStrategy: value as any }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="first">First Option</SelectItem>
                      <SelectItem value="last">Last Option</SelectItem>
                      <SelectItem value="random">Random Option</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </>
          )}

          {(formData.type === 'smart' || formData.type === 'conversation_analysis') && (
            <div>
              <Label>Routing Options</Label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <Input
                    placeholder="Agent/Tool name"
                    value={routingOptionKey}
                    onChange={(e) => setRoutingOptionKey(e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    placeholder="Description of when to route here"
                    value={routingOptionValue}
                    onChange={(e) => setRoutingOptionValue(e.target.value)}
                    className="flex-2"
                  />
                  <Button type="button" onClick={addRoutingOption} variant="outline">
                    Add
                  </Button>
                </div>
                
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {Object.entries(formData.routingOptions).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="text-sm">
                        <span className="font-medium">{key}:</span> {value}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeRoutingOption(key)}
                        className="text-red-600 hover:text-red-800"
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeRouterEditor}>
              Cancel
            </Button>
            <Button type="submit">
              {isNewRouter ? 'Create Router' : 'Update Router'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default RouterEditor;
