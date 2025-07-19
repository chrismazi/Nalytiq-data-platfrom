"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  {
    name: "2018",
    lifeExpectancy: 67.5,
    infantMortality: 32.4,
    vaccinationRate: 87.2,
  },
  {
    name: "2019",
    lifeExpectancy: 68.1,
    infantMortality: 30.8,
    vaccinationRate: 88.9,
  },
  {
    name: "2020",
    lifeExpectancy: 68.4,
    infantMortality: 29.5,
    vaccinationRate: 89.7,
  },
  {
    name: "2021",
    lifeExpectancy: 68.8,
    infantMortality: 28.3,
    vaccinationRate: 90.8,
  },
  {
    name: "2022",
    lifeExpectancy: 69.2,
    infantMortality: 27.1,
    vaccinationRate: 92.4,
  },
]

interface HealthMetricsChartProps {
  height?: number
}

export function HealthMetricsChart({ height = 220 }: HealthMetricsChartProps) {
  return (
    <ChartContainer
      config={{
        height,
        margin: { top: 20, right: 5, left: 5, bottom: 20 },
      }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis fontSize={12} tickLine={false} axisLine={false} />
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
                          label: "Life Expectancy",
                          value: `${payload[0].value} years`,
                        },
                        {
                          label: "Infant Mortality",
                          value: `${payload[1].value} per 1,000`,
                        },
                        {
                          label: "Vaccination Rate",
                          value: `${payload[2].value}%`,
                        },
                      ]}
                    />
                  </ChartTooltip>
                )
              }
              return null
            }}
          />
          <Legend />
          <Bar
            dataKey="lifeExpectancy"
            name="Life Expectancy (years)"
            fill="hsl(var(--primary))"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="infantMortality"
            name="Infant Mortality (per 1,000)"
            fill="hsl(var(--destructive))"
            radius={[4, 4, 0, 0]}
          />
          <Bar dataKey="vaccinationRate" name="Vaccination Rate (%)" fill="hsl(var(--accent))" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
