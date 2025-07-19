"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { name: "2018", gdp: 6.1 },
  { name: "2019", gdp: 9.5 },
  { name: "2020", gdp: -3.4 },
  { name: "2021", gdp: 10.9 },
  { name: "2022", gdp: 8.2 },
  { name: "2023", gdp: 7.8 },
]

interface GDPChartProps {
  height?: number
}

export function GDPChart({ height = 180 }: GDPChartProps) {
  return (
    <ChartContainer
      config={{
        height,
        margin: { top: 5, right: 5, left: 5, bottom: 20 },
      }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
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
                          label: "Year",
                          value: payload[0].payload.name,
                        },
                        {
                          label: "GDP Growth",
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
          <Line
            type="monotone"
            dataKey="gdp"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            dot={{ r: 4, strokeWidth: 2 }}
            activeDot={{ r: 6, strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
