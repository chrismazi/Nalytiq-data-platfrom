"use client"

import { useState } from "react"
import { Download, Plus, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"

export function CrossTabBuilder() {
  const [variables, setVariables] = useState<string[]>(["province"])
  const [showTable, setShowTable] = useState(false)

  const addVariable = () => {
    setVariables([...variables, ""])
  }

  const removeVariable = (index: number) => {
    const newVariables = [...variables]
    newVariables.splice(index, 1)
    setVariables(newVariables)
  }

  const updateVariable = (index: number, value: string) => {
    const newVariables = [...variables]
    newVariables[index] = value
    setVariables(newVariables)
  }

  const generateTable = () => {
    setShowTable(true)
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex flex-col gap-4">
          {variables.map((variable, index) => (
            <div key={index} className="flex items-center gap-2">
              <div className="flex-1">
                <label className="text-sm font-medium mb-1 block">
                  {index === 0 ? "Row Variable" : index === 1 ? "Column Variable" : `Additional Variable ${index}`}
                </label>
                <Select value={variable} onValueChange={(value) => updateVariable(index, value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select Variable" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="province">Province</SelectItem>
                    <SelectItem value="gender">Gender</SelectItem>
                    <SelectItem value="age_group">Age Group</SelectItem>
                    <SelectItem value="education">Education Level</SelectItem>
                    <SelectItem value="income">Income Bracket</SelectItem>
                    <SelectItem value="has_electricity">Electricity Access</SelectItem>
                    <SelectItem value="has_water">Water Access</SelectItem>
                    <SelectItem value="has_internet">Internet Access</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {variables.length > 1 && (
                <Button variant="ghost" size="icon" onClick={() => removeVariable(index)} className="mt-6">
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={addVariable} disabled={variables.length >= 3}>
            <Plus className="h-4 w-4 mr-2" />
            Add Variable
          </Button>
          <Button size="sm" onClick={generateTable}>
            Generate Table
          </Button>
        </div>
      </div>

      {showTable && (
        <Card>
          <CardContent className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-medium text-lg">Cross-Tabulation: {variables.join(" × ")}</h3>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
            <DataTable />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
