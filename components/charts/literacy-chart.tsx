"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { name: "Literate", value: 73.2 },
  { name: "Illiterate", value: 26.8 },
]

const COLORS = ["hsl(var(--primary))", "hsl(var(--muted))"]

interface LiteracyChartProps {
  height?: number
}

export function LiteracyChart({ height = 180 }: LiteracyChartProps) {
  return (
    <ChartContainer
      config={{
        height,
        margin: { top: 5, right: 5, left: 5, bottom: 5 },
      }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={height > 200 ? 60 : 40}
            outerRadius={height > 200 ? 80 : 60}
            paddingAngle={2}
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <ChartTooltip>
                    <ChartTooltipContent
                      content={[
                        {
                          label: "Category",
                          value: payload[0].name,
                        },
                        {
                          label: "Percentage",
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
        </PieChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
