"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export function DataTable() {
  // Sample data for province distribution
  const data = [
    { province: "Kigali City", population: 1_132_686, percentage: 8.6, growth: 4.2 },
    { province: "Southern", population: 2_589_975, percentage: 19.6, growth: 1.8 },
    { province: "Western", population: 2_471_239, percentage: 18.7, growth: 2.1 },
    { province: "Northern", population: 1_865_454, percentage: 14.1, growth: 1.9 },
    { province: "Eastern", population: 2_595_703, percentage: 19.7, growth: 2.6 },
  ]

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Province</TableHead>
            <TableHead className="text-right">Population</TableHead>
            <TableHead className="text-right">Percentage</TableHead>
            <TableHead className="text-right">Growth Rate</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.province}>
              <TableCell className="font-medium">{row.province}</TableCell>
              <TableCell className="text-right">{row.population.toLocaleString()}</TableCell>
              <TableCell className="text-right">{row.percentage}%</TableCell>
              <TableCell className="text-right">
                <Badge
                  variant="outline"
                  className={
                    row.growth > 2.5 ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300" : ""
                  }
                >
                  {row.growth}%
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
