import React from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
} from 'reactflow';


import { CustomEdgeData } from '@/types/reactflow';

const CustomEdge: React.FC<EdgeProps<CustomEdgeData>> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Generate unique marker ID for this edge
  const markerId = `arrow-${id}`;



  return (
    <>
      {/* Arrow marker definition */}
      <defs>
        <marker
          id={markerId}
          viewBox="0 0 20 20"
          refX="18"
          refY="10"
          markerWidth="10"
          markerHeight="10"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path
            d="M0,0 L0,20 L20,10 z"
            fill={selected ? '#3b82f6' : '#64748b'}
          />
        </marker>
      </defs>
      
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: selected ? '#3b82f6' : '#64748b',
          strokeWidth: selected ? 3 : 2,
          markerEnd: `url(#${markerId})`,
        }}
      />
      {data?.router && (
        <EdgeLabelRenderer>
          <div
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              position: 'absolute',
              fontSize: 10,
              pointerEvents: 'none',
            }}
            className="edge-label"
          >
            <div className="bg-white border rounded-md shadow-sm px-2 py-1">
              <span className="text-xs text-blue-600 font-medium">
                {data.router}
              </span>
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};

export default CustomEdge;
