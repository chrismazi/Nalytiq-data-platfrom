/**
 * Data export utilities for CSV, Excel, and JSON
 */

export type ExportFormat = 'csv' | 'excel' | 'json' | 'pdf'

interface ExportOptions {
  filename?: string
  includeHeaders?: boolean
  selectedColumns?: string[]
  dateFormat?: string
}

/**
 * Export data to CSV format
 */
export function exportToCSV(
  data: any[],
  options: ExportOptions = {}
): void {
  const {
    filename = 'export.csv',
    includeHeaders = true,
    selectedColumns,
  } = options

  if (!data || data.length === 0) {
    throw new Error('No data to export')
  }

  // Get columns from first row or use selected columns
  const columns = selectedColumns || Object.keys(data[0])

  // Build CSV content
  let csv = ''

  // Add headers
  if (includeHeaders) {
    csv += columns.map(escapeCSVValue).join(',') + '\n'
  }

  // Add rows
  data.forEach((row) => {
    const values = columns.map((col) => {
      const value = row[col]
      return escapeCSVValue(value)
    })
    csv += values.join(',') + '\n'
  })

  // Download file
  downloadFile(csv, filename, 'text/csv;charset=utf-8;')
}

/**
 * Export data to JSON format
 */
export function exportToJSON(
  data: any[],
  options: ExportOptions = {}
): void {
  const {
    filename = 'export.json',
    selectedColumns,
  } = options

  if (!data || data.length === 0) {
    throw new Error('No data to export')
  }

  // Filter columns if specified
  let exportData = data
  if (selectedColumns && selectedColumns.length > 0) {
    exportData = data.map((row) => {
      const filtered: any = {}
      selectedColumns.forEach((col) => {
        if (col in row) {
          filtered[col] = row[col]
        }
      })
      return filtered
    })
  }

  // Convert to JSON
  const json = JSON.stringify(exportData, null, 2)

  // Download file
  downloadFile(json, filename, 'application/json;charset=utf-8;')
}

/**
 * Export table data to Excel-compatible CSV
 * (for better Excel compatibility with special characters)
 */
export function exportToExcel(
  data: any[],
  options: ExportOptions = {}
): void {
  const filename = options.filename?.replace('.csv', '.xlsx') || 'export.xlsx'
  
  // For now, use CSV with UTF-8 BOM for Excel compatibility
  // In the future, this can be enhanced with a library like xlsx
  const {
    includeHeaders = true,
    selectedColumns,
  } = options

  if (!data || data.length === 0) {
    throw new Error('No data to export')
  }

  const columns = selectedColumns || Object.keys(data[0])

  // Add UTF-8 BOM for Excel
  let csv = '\uFEFF'

  // Add headers
  if (includeHeaders) {
    csv += columns.map(escapeCSVValue).join(',') + '\n'
  }

  // Add rows
  data.forEach((row) => {
    const values = columns.map((col) => {
      const value = row[col]
      return escapeCSVValue(value)
    })
    csv += values.join(',') + '\n'
  })

  // Download file
  downloadFile(csv, filename, 'text/csv;charset=utf-8;')
}

/**
 * Escape CSV values
 */
function escapeCSVValue(value: any): string {
  if (value === null || value === undefined) {
    return ''
  }

  const stringValue = String(value)

  // If value contains comma, quote, or newline, wrap in quotes
  if (
    stringValue.includes(',') ||
    stringValue.includes('"') ||
    stringValue.includes('\n') ||
    stringValue.includes('\r')
  ) {
    return `"${stringValue.replace(/"/g, '""')}"`
  }

  return stringValue
}

/**
 * Download file helper
 */
function downloadFile(
  content: string,
  filename: string,
  mimeType: string
): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Format data for export (handle dates, numbers, etc.)
 */
export function formatDataForExport(
  data: any[],
  dateFormat: string = 'YYYY-MM-DD'
): any[] {
  return data.map((row) => {
    const formatted: any = {}
    
    Object.keys(row).forEach((key) => {
      const value = row[key]
      
      // Handle dates
      if (value instanceof Date) {
        formatted[key] = formatDate(value, dateFormat)
      }
      // Handle null/undefined
      else if (value === null || value === undefined) {
        formatted[key] = ''
      }
      // Handle numbers
      else if (typeof value === 'number') {
        formatted[key] = isNaN(value) ? '' : value
      }
      // Handle booleans
      else if (typeof value === 'boolean') {
        formatted[key] = value ? 'Yes' : 'No'
      }
      // Default
      else {
        formatted[key] = value
      }
    })
    
    return formatted
  })
}

/**
 * Simple date formatter
 */
function formatDate(date: Date, format: string): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * Export chart data
 */
export function exportChartData(
  chartData: any,
  format: ExportFormat = 'csv',
  filename?: string
): void {
  // Convert chart data to table format
  const tableData = convertChartDataToTable(chartData)
  
  switch (format) {
    case 'csv':
      exportToCSV(tableData, { filename })
      break
    case 'excel':
      exportToExcel(tableData, { filename })
      break
    case 'json':
      exportToJSON(tableData, { filename })
      break
    default:
      throw new Error(`Unsupported export format: ${format}`)
  }
}

/**
 * Convert chart data to table format
 */
function convertChartDataToTable(chartData: any): any[] {
  if (Array.isArray(chartData)) {
    return chartData
  }

  // Handle Recharts data format
  if (chartData.data && Array.isArray(chartData.data)) {
    return chartData.data
  }

  // Handle other formats
  return [chartData]
}

/**
 * Copy data to clipboard
 */
export async function copyToClipboard(data: any[]): Promise<void> {
  const csv = data.map((row) => {
    return Object.values(row).map(escapeCSVValue).join('\t')
  }).join('\n')

  try {
    await navigator.clipboard.writeText(csv)
  } catch (err) {
    // Fallback for older browsers
    const textarea = document.createElement('textarea')
    textarea.value = csv
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
}

/**
 * Get export filename with timestamp
 */
export function getExportFilename(
  baseName: string,
  format: ExportFormat
): string {
  const timestamp = new Date()
    .toISOString()
    .replace(/[:.]/g, '-')
    .substring(0, 19)
  
  const extension = format === 'excel' ? 'xlsx' : format
  return `${baseName}_${timestamp}.${extension}`
}
