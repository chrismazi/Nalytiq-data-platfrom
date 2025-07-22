"use client"

import { useState } from "react"
import { Check, Download, FileText, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

interface GenerateReportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  isGenerating: boolean
}

export function GenerateReportDialog({ open, onOpenChange, isGenerating }: GenerateReportDialogProps) {
  const [progress, setProgress] = useState(0)
  const [completed, setCompleted] = useState(false)

  // Simulate progress
  if (isGenerating && progress < 100) {
    setTimeout(() => {
      setProgress((prev) => {
        if (prev >= 100) return 100
        return prev + 5
      })
    }, 150)
  }

  if (progress >= 100 && !completed) {
    setTimeout(() => {
      setCompleted(true)
    }, 500)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Generate AI Report</DialogTitle>
          <DialogDescription>Create an AI-generated report based on the current dashboard data</DialogDescription>
        </DialogHeader>

        {!completed ? (
          <div className="space-y-6 py-4">
            {isGenerating ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <div className="flex-1">
                    <p className="font-medium">Generating your report</p>
                    <p className="text-sm text-muted-foreground">Analyzing data and creating insights...</p>
                  </div>
                </div>
                <Progress value={progress} />
                <p className="text-xs text-muted-foreground text-center">
                  {progress < 30 && "Analyzing trends..."}
                  {progress >= 30 && progress < 60 && "Generating visualizations..."}
                  {progress >= 60 && progress < 90 && "Creating narrative explanations..."}
                  {progress >= 90 && "Finalizing report..."}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-medium">Include in report:</h3>
                  <div className="space-y-2">
                    {[
                      "Executive Summary",
                      "Key Indicators Analysis",
                      "Trend Visualizations",
                      "Regional Comparisons",
                      "Recommendations",
                    ].map((item, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <Checkbox id={`item-${index}`} defaultChecked={index < 3} />
                        <Label htmlFor={`item-${index}`}>{item}</Label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6 py-4">
            <div className="flex flex-col items-center justify-center text-center">
              <div className="rounded-full bg-green-100 dark:bg-green-900/30 p-3 mb-4">
                <Check className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-medium mb-1">Report Generated Successfully</h3>
              <p className="text-sm text-muted-foreground mb-4">Your AI-generated report is ready to download</p>
              <div className="flex items-center justify-center gap-3 p-4 border rounded-lg bg-muted/50 w-full">
                <FileText className="h-8 w-8 text-primary" />
                <div className="text-left">
                  <p className="font-medium">Nalytiq Dashboard Report</p>
                  <p className="text-xs text-muted-foreground">PDF • 2.4 MB • Generated on May 3, 2023</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <DialogFooter className="flex items-center justify-between sm:justify-between">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {completed ? "Close" : "Cancel"}
          </Button>
          <Button disabled={isGenerating}>
            {completed ? (
              <>
                <Download className="mr-2 h-4 w-4" />
                Download Report
              </>
            ) : (
              "Generate Report"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
