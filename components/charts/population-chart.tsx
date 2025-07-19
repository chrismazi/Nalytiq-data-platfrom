"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { name: "2018", population: 12.3 },
  { name: "2019", population: 12.6 },
  { name: "2020", population: 12.9 },
  { name: "2021", population: 13.0 },
  { name: "2022", population: 13.2 },
  { name: "2023", population: 13.5 },
]

interface PopulationChartProps {
  height?: number
}

export function PopulationChart({ height = 180 }: PopulationChartProps) {
  return (
    <ChartContainer
      config={{
        height,
        margin: { top: 5, right: 5, left: 5, bottom: 20 },
      }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}M`} />
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
                          label: "Population",
                          value: `${payload[0].value}M`,
                        },
                      ]}
                    />
                  </ChartTooltip>
                )
              }
              return null
            }}
          />
          <Bar dataKey="population" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
