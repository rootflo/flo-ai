import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useDesignerStore } from '@/store/designerStore';

const EdgeEditor: React.FC = () => {
  const {
    isEdgeEditorOpen,
    closeEdgeEditor,
    selectedEdge,
    updateEdge,
    config,
  } = useDesignerStore();

  const [formData, setFormData] = useState({
    router: 'none',
    label: '',
    description: '',
  });

  useEffect(() => {
    if (selectedEdge) {
      setFormData({
        router: selectedEdge.data?.router || 'none',
        label: selectedEdge.data?.label || '',
        description: '',
      });
    }
  }, [selectedEdge]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedEdge) {
      updateEdge(selectedEdge.id, {
        ...selectedEdge,
        data: {
          ...selectedEdge.data,
          router: formData.router === 'none' ? undefined : formData.router,
          label: formData.router === 'none' ? (formData.label || undefined) : formData.router,
        },
      });
    }
    closeEdgeEditor();
  };

  const selectedRouterConfig = formData.router !== 'none' 
    ? config.availableRouters.find((router) => router.name === formData.router)
    : null;

  return (
    <Dialog open={isEdgeEditorOpen} onOpenChange={closeEdgeEditor}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Configure Edge Router</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label>Router Function</Label>
            <Select
              value={formData.router}
              onValueChange={(value) => setFormData(prev => ({ ...prev, router: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a router function" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No router (direct connection)</SelectItem>
                {config.availableRouters.map((router) => (
                  <SelectItem key={router.name} value={router.name}>
                    {router.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedRouterConfig && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-sm text-gray-800 mb-2">
                Router Description
              </h4>
              <p className="text-sm text-gray-600">
                {selectedRouterConfig.description}
              </p>
              {selectedRouterConfig.code && (
                <div className="mt-3">
                  <Label className="text-xs text-gray-500">Implementation:</Label>
                  <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                    {selectedRouterConfig.code}
                  </pre>
                </div>
              )}
            </div>
          )}

          <div>
            <Label>Connection Notes (Optional)</Label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Add notes about this connection..."
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeEdgeEditor}>
              Cancel
            </Button>
            <Button type="submit">Update Connection</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default EdgeEditor;
