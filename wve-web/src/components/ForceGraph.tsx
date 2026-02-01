import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { GraphData } from '../types';

interface ForceGraphProps {
  data: GraphData;
  height?: number;
  onNodeClick?: (nodeId: string) => void;
}

export const ForceGraph: React.FC<ForceGraphProps> = ({
  data,
  height = 500,
  onNodeClick,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return;

    const width = svgRef.current.clientWidth;

    // Create a copy of data to avoid mutations
    const nodes = data.nodes.map((d) => ({ ...d })) as any[];
    const links = data.links.map((d) => ({ ...d })) as any[];

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Create SVG
    const svg = d3.select(svgRef.current);

    // Add zoom behavior
    const g = svg.append('g');

    const zoom = d3.zoom().on('zoom', (event: any) => {
      g.attr('transform', event.transform);
    });

    svg.call(zoom as any);

    // Create force simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Create links
    const link = g
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('class', 'graph-link')
      .attr('stroke-width', (d: any) => Math.sqrt(d.weight) * 2);

    // Create nodes
    const nodeGroup = g
      .selectAll('g.graph-node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'graph-node')
      .call(
        d3
          .drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended) as any
      );

    // Add circles for nodes
    nodeGroup
      .append('circle')
      .attr('r', (d: any) => {
        if (d.type === 'belief') {
          return 8 + (d.confidence ? d.confidence * 5 : 0);
        }
        return 6;
      })
      .attr('fill', (d: any) => {
        if (d.type === 'belief') return '#3b82f6';
        return '#10b981';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event, d: any) => {
        event.stopPropagation();
        onNodeClick?.(d.id);
      });

    // Add labels
    nodeGroup
      .append('text')
      .attr('class', 'graph-node-label')
      .attr('dy', '0.3em')
      .text((d: any) => d.label)
      .style('font-size', (d: any) =>
        d.type === 'belief' ? '11px' : '10px'
      )
      .style('font-weight', (d: any) =>
        d.type === 'belief' ? '600' : '400'
      );

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: any): void {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any): void {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any): void {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [data, height, onNodeClick]);

  return (
    <svg
      ref={svgRef}
      className="force-graph border border-gray-200 rounded-lg"
      style={{ height: `${height}px`, width: '100%' }}
    />
  );
};
