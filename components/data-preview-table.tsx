"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

type Column = { name: string; type?: string; description?: string }

type DataPreviewTableProps = {
  columns: Column[]
  data: any[]
}

export function DataPreviewTable({ columns, data }: DataPreviewTableProps) {
  if (!columns || columns.length === 0 || !data || data.length === 0) {
    console.warn("DataPreviewTable: No columns or data provided.", { columns, data });
    return (
      <div className="border rounded-md p-4 text-center text-muted-foreground">
        No data to preview. Please upload a valid CSV file.
      </div>
    );
  }

  return (
    <div className="border rounded-md">
      <div className="border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-medium">Data Preview</h3>
          <p className="text-sm text-muted-foreground">Showing {data.length} row{data.length > 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          {[...new Set(columns.map((col) => col.type || "string"))].map((type) => (
            <Badge key={type} variant="outline" className="capitalize">
              {type}
            </Badge>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead key={column.name} className="whitespace-nowrap">
                  <div className="font-medium">{column.name}</div>
                  <div className="text-xs text-muted-foreground">{column.type}</div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {columns.map((column) => (
                  <TableCell key={`${rowIndex}-${column.name}`} className="whitespace-nowrap">
                    {typeof row[column.name] === "boolean"
                      ? row[column.name]
                        ? "Yes"
                        : "No"
                      : String(row[column.name] ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
