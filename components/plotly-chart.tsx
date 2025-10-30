"use client"

import { useEffect, useRef } from "react"
import dynamic from "next/dynamic"

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false })

interface PlotlyChartProps {
  data: any
  layout?: any
  config?: any
  className?: string
  onHover?: (event: any) => void
  onClick?: (event: any) => void
}

export function PlotlyChart({ 
  data, 
  layout = {}, 
  config = {},
  className = "",
  onHover,
  onClick
}: PlotlyChartProps) {
  const defaultLayout = {
    autosize: true,
    margin: { t: 50, r: 50, b: 50, l: 50 },
    template: 'plotly_white',
    hovermode: 'closest',
    ...layout
  }

  const defaultConfig = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    responsive: true,
    ...config
  }

  // If data is from our API (has nested structure), extract it
  const plotData = data?.data?.data || data?.data || data

  return (
    <div className={`plotly-chart-container ${className}`}>
      <Plot
        data={plotData}
        layout={defaultLayout}
        config={defaultConfig}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
        onHover={onHover}
        onClick={onClick}
      />
    </div>
  )
}

// Simpler wrapper that accepts our backend response directly
export function PlotlyChartFromAPI({ chart, className = "" }: { chart: any, className?: string }) {
  if (!chart?.data) {
    return <div className="text-muted-foreground">No chart data available</div>
  }

  return <PlotlyChart data={chart.data} className={className} />
}
