"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
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
    <ChartContainer config={{}}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barCategoryGap={30}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="name" fontSize={14} tickLine={false} axisLine={false} dy={8} />
          <YAxis fontSize={14} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}M`} dx={-8} />
          <Tooltip />
          <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 13 }} />
          <Bar dataKey="population" name="Population (M)" fill="#2563eb" radius={[8, 8, 0, 0]} maxBarSize={40} />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
