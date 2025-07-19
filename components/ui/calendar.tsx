"use client"

import * as React from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { DayPicker } from "react-day-picker"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

export type CalendarProps = React.ComponentProps<typeof DayPicker>

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        root: "rdp-root",
        months: "flex flex-col sm:flex-row gap-8 sm:gap-8 bg-transparent",
        month: "bg-white border rounded-xl shadow-md p-4 relative min-w-[320px]",
        month_grid: "w-full border-collapse",
        caption: "flex justify-between items-center mb-2 px-2",
        caption_label: "text-base font-semibold text-gray-800 aria-label:sr-only",
        nav: "flex items-center justify-between w-full absolute top-2 left-0 right-0 px-2 z-10",
        button_previous: cn(buttonVariants({ variant: "ghost" }), "h-8 w-8 p-0 text-gray-500 hover:bg-gray-100 rounded-full", "absolute left-2 top-2"),
        button_next: cn(buttonVariants({ variant: "ghost" }), "h-8 w-8 p-0 text-gray-500 hover:bg-gray-100 rounded-full", "absolute right-2 top-2"),
        weekdays: "table-row",
        weekday: "text-muted-foreground w-9 font-normal text-[0.9rem] text-center p-0",
        week: "table-row",
        day: cn(
          buttonVariants({ variant: "ghost" }),
          "h-9 w-9 p-0 font-normal aria-selected:opacity-100 text-gray-900 transition-colors duration-150",
          "hover:bg-[#EAEEFE] focus:bg-[#EAEEFE] focus:outline-none"
        ),
        selected: "bg-[#EAEEFE] text-primary-foreground border border-primary",
        today: "bg-accent text-accent-foreground border border-primary",
        outside: "opacity-40 text-gray-400 cursor-default",
        disabled: "text-muted-foreground opacity-50 cursor-not-allowed",
        hidden: "invisible",
        ...classNames,
      }}
      formatters={{
        formatCaption: (month) => month.toLocaleString('default', { month: 'long', year: 'numeric' }),
        labelDay: (date, options) => `${date.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}${options.selected ? ', selected' : ''}${options.today ? ', today' : ''}`,
      }}
      labels={{
        labelPrevious: "Previous Month",
        labelNext: "Next Month",
      }}
      components={{
        // Custom navigation buttons with tooltips
        ButtonPrevious: (props) => (
          <button {...props} aria-label="Previous Month" title="Previous Month" className="h-8 w-8 p-0 text-gray-500 hover:bg-gray-100 rounded-full absolute left-2 top-2 flex items-center justify-center">
            <ChevronLeft className="h-4 w-4" />
          </button>
        ),
        ButtonNext: (props) => (
          <button {...props} aria-label="Next Month" title="Next Month" className="h-8 w-8 p-0 text-gray-500 hover:bg-gray-100 rounded-full absolute right-2 top-2 flex items-center justify-center">
            <ChevronRight className="h-4 w-4" />
          </button>
        ),
      }}
      {...props}
    />
  )
}
Calendar.displayName = "Calendar"

export { Calendar }
