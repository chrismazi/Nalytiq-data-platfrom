"use client"

import { useState } from "react"
import { Download, FileSpreadsheet, FileJson, FileText, Copy, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { toast } from "@/lib/toast"
import {
  exportToCSV,
  exportToJSON,
  exportToExcel,
  copyToClipboard,
  getExportFilename,
  type ExportFormat,
} from "@/lib/export-utils"

interface ExportButtonProps {
  data: any[]
  filename?: string
  variant?: "default" | "outline" | "ghost"
  size?: "default" | "sm" | "lg" | "icon"
  className?: string
  disabled?: boolean
  showCopyOption?: boolean
}

export function ExportButton({
  data,
  filename = "export",
  variant = "outline",
  size = "default",
  className,
  disabled = false,
  showCopyOption = true,
}: ExportButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleExport = async (format: ExportFormat) => {
    if (!data || data.length === 0) {
      toast.error("No data to export")
      return
    }

    try {
      const exportFilename = getExportFilename(filename, format)

      switch (format) {
        case "csv":
          exportToCSV(data, { filename: exportFilename })
          toast.success(`Exported ${data.length} rows to CSV`)
          break
        case "excel":
          exportToExcel(data, { filename: exportFilename })
          toast.success(`Exported ${data.length} rows to Excel`)
          break
        case "json":
          exportToJSON(data, { filename: exportFilename })
          toast.success(`Exported ${data.length} rows to JSON`)
          break
        default:
          toast.error(`Unsupported format: ${format}`)
      }
    } catch (error) {
      console.error("Export failed:", error)
      toast.error("Failed to export data")
    }
  }

  const handleCopy = async () => {
    try {
      await copyToClipboard(data)
      setCopied(true)
      toast.success("Data copied to clipboard")
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error("Copy failed:", error)
      toast.error("Failed to copy data")
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          size={size}
          className={className}
          disabled={disabled || !data || data.length === 0}
        >
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel>Export as...</DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={() => handleExport("csv")}>
          <FileText className="h-4 w-4 mr-2" />
          CSV File
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => handleExport("excel")}>
          <FileSpreadsheet className="h-4 w-4 mr-2" />
          Excel File
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => handleExport("json")}>
          <FileJson className="h-4 w-4 mr-2" />
          JSON File
        </DropdownMenuItem>
        
        {showCopyOption && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleCopy}>
              {copied ? (
                <Check className="h-4 w-4 mr-2 text-green-500" />
              ) : (
                <Copy className="h-4 w-4 mr-2" />
              )}
              {copied ? "Copied!" : "Copy to Clipboard"}
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// Simple export button without dropdown
export function QuickExportButton({
  data,
  format = "csv",
  filename = "export",
  children,
  ...props
}: {
  data: any[]
  format?: ExportFormat
  filename?: string
  children?: React.ReactNode
} & React.ComponentProps<typeof Button>) {
  const handleExport = () => {
    if (!data || data.length === 0) {
      toast.error("No data to export")
      return
    }

    try {
      const exportFilename = getExportFilename(filename, format)

      switch (format) {
        case "csv":
          exportToCSV(data, { filename: exportFilename })
          break
        case "excel":
          exportToExcel(data, { filename: exportFilename })
          break
        case "json":
          exportToJSON(data, { filename: exportFilename })
          break
      }

      toast.success(`Data exported successfully`)
    } catch (error) {
      console.error("Export failed:", error)
      toast.error("Failed to export data")
    }
  }

  return (
    <Button onClick={handleExport} {...props}>
      <Download className="h-4 w-4 mr-2" />
      {children || "Export"}
    </Button>
  )
}
