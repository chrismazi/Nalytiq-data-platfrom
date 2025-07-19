"use client"

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { name: "Jan", inflation: 3.5 },
  { name: "Feb", inflation: 3.7 },
  { name: "Mar", inflation: 3.9 },
  { name: "Apr", inflation: 4.2 },
  { name: "May", inflation: 4.0 },
  { name: "Jun", inflation: 3.8 },
]

interface InflationChartProps {
  height?: number
}

export function InflationChart({ height = 180 }: InflationChartProps) {
  return (
    <ChartContainer
      config={{
        height,
        margin: { top: 5, right: 5, left: 5, bottom: 20 },
      }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}%`} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <ChartTooltip>
                    <ChartTooltipContent
                      content={[
                        {
                          label: "Month",
                          value: payload[0].payload.name,
                        },
                        {
                          label: "Inflation Rate",
                          value: `${payload[0].value}%`,
                        },
                      ]}
                    />
                  </ChartTooltip>
                )
              }
              return null
            }}
          />
          <Area
            type="monotone"
            dataKey="inflation"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary) / 0.2)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
