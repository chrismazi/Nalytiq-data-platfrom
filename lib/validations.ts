/**
 * Zod validation schemas for forms and data
 */

import { z } from "zod"

// ============================================================================
// Authentication Schemas
// ============================================================================

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Invalid email address")
    .toLowerCase()
    .trim(),
  password: z
    .string()
    .min(1, "Password is required")
    .min(8, "Password must be at least 8 characters"),
})

export const registerSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Invalid email address")
    .toLowerCase()
    .trim(),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .max(100, "Password is too long")
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain at least one uppercase letter, one lowercase letter, and one number"
    ),
  confirmPassword: z.string().min(1, "Please confirm your password"),
  role: z.enum(["admin", "analyst", "viewer"], {
    required_error: "Please select a role",
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
})

export const changePasswordSchema = z.object({
  currentPassword: z.string().min(1, "Current password is required"),
  newPassword: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain uppercase, lowercase, and number"
    ),
  confirmPassword: z.string().min(1, "Please confirm your password"),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
})

// ============================================================================
// File Upload Schemas
// ============================================================================

export const fileUploadSchema = z.object({
  file: z
    .instanceof(File)
    .refine((file) => file.size > 0, "File cannot be empty")
    .refine(
      (file) => file.size <= 500 * 1024 * 1024, // 500MB
      "File size must be less than 500MB"
    )
    .refine(
      (file) => {
        const extension = file.name.split(".").pop()?.toLowerCase()
        return ["csv", "xlsx", "xls", "dta"].includes(extension || "")
      },
      "Invalid file type. Allowed: CSV, Excel, Stata"
    ),
  description: z.string().optional(),
})

// ============================================================================
// Data Analysis Schemas
// ============================================================================

export const groupedStatsSchema = z.object({
  groupBy: z.string().min(1, "Group by column is required"),
  value: z.string().min(1, "Value column is required"),
  aggregation: z.enum(["mean", "sum", "count", "min", "max", "median", "std"], {
    required_error: "Please select an aggregation function",
  }),
})

export const crosstabSchema = z.object({
  columns: z
    .array(z.string())
    .min(1, "Select at least one column")
    .max(2, "Select at most two columns"),
  showPercentages: z.boolean().optional().default(false),
  showTotals: z.boolean().optional().default(true),
})

export const modelingSchema = z.object({
  target: z.string().min(1, "Target variable is required"),
  features: z
    .array(z.string())
    .min(1, "Select at least one feature")
    .max(50, "Too many features selected (max 50)"),
  modelType: z.enum(["classification", "regression"], {
    required_error: "Select model type",
  }),
  testSize: z
    .number()
    .min(0.1, "Test size must be at least 10%")
    .max(0.5, "Test size must be at most 50%")
    .default(0.2),
})

// ============================================================================
// Report Generation Schemas
// ============================================================================

export const reportGenerationSchema = z.object({
  title: z
    .string()
    .min(1, "Report title is required")
    .max(200, "Title is too long"),
  description: z.string().optional(),
  includeExecutiveSummary: z.boolean().default(true),
  includeVisualization: z.boolean().default(true),
  includeStatistics: z.boolean().default(true),
  includeRecommendations: z.boolean().default(true),
  format: z.enum(["pdf", "excel", "html"], {
    required_error: "Select output format",
  }),
  dateRange: z
    .object({
      from: z.date().optional(),
      to: z.date().optional(),
    })
    .optional(),
})

// ============================================================================
// User Profile Schemas
// ============================================================================

export const userProfileSchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name is too long")
    .optional(),
  organization: z.string().max(200, "Organization name is too long").optional(),
  phone: z
    .string()
    .regex(/^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/, "Invalid phone number")
    .optional()
    .or(z.literal("")),
  bio: z.string().max(500, "Bio is too long").optional(),
})

// ============================================================================
// Search and Filter Schemas
// ============================================================================

export const searchSchema = z.object({
  query: z.string().min(1, "Search query is required").max(200),
  filters: z
    .object({
      dateFrom: z.date().optional(),
      dateTo: z.date().optional(),
      category: z.string().optional(),
      status: z.string().optional(),
    })
    .optional(),
  sortBy: z.enum(["date", "name", "size", "relevance"]).optional(),
  sortOrder: z.enum(["asc", "desc"]).optional().default("desc"),
})

export const filterSchema = z.object({
  columns: z.array(z.string()).optional(),
  minValue: z.number().optional(),
  maxValue: z.number().optional(),
  includeNulls: z.boolean().default(true),
  caseSensitive: z.boolean().default(false),
})

// ============================================================================
// Export Schemas
// ============================================================================

export const exportSchema = z.object({
  format: z.enum(["csv", "excel", "pdf", "json"], {
    required_error: "Select export format",
  }),
  includeHeaders: z.boolean().default(true),
  selectedColumns: z.array(z.string()).optional(),
  maxRows: z.number().min(1).max(1000000).optional(),
  filename: z
    .string()
    .min(1, "Filename is required")
    .max(200, "Filename is too long")
    .regex(/^[a-zA-Z0-9_-]+$/, "Filename can only contain letters, numbers, hyphens, and underscores"),
})

// ============================================================================
// Chatbot Schemas
// ============================================================================

export const chatbotQuerySchema = z.object({
  question: z
    .string()
    .min(1, "Question is required")
    .max(500, "Question is too long"),
  context: z.record(z.any()).optional(),
  conversationId: z.string().optional(),
})

// ============================================================================
// Type Exports
// ============================================================================

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>
export type FileUploadInput = z.infer<typeof fileUploadSchema>
export type GroupedStatsInput = z.infer<typeof groupedStatsSchema>
export type CrosstabInput = z.infer<typeof crosstabSchema>
export type ModelingInput = z.infer<typeof modelingSchema>
export type ReportGenerationInput = z.infer<typeof reportGenerationSchema>
export type UserProfileInput = z.infer<typeof userProfileSchema>
export type SearchInput = z.infer<typeof searchSchema>
export type FilterInput = z.infer<typeof filterSchema>
export type ExportInput = z.infer<typeof exportSchema>
export type ChatbotQueryInput = z.infer<typeof chatbotQuerySchema>

// ============================================================================
// Validation Helper Functions
// ============================================================================

export function validateEmail(email: string): boolean {
  return loginSchema.shape.email.safeParse(email).success
}

export function validatePassword(password: string): boolean {
  const passwordSchema = z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must contain uppercase, lowercase, and number"
    )
  return passwordSchema.safeParse(password).success
}

export function getPasswordStrength(password: string): {
  strength: "weak" | "medium" | "strong"
  score: number
} {
  let score = 0

  if (password.length >= 8) score += 1
  if (password.length >= 12) score += 1
  if (/[a-z]/.test(password)) score += 1
  if (/[A-Z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1

  if (score <= 2) return { strength: "weak", score }
  if (score <= 4) return { strength: "medium", score }
  return { strength: "strong", score }
}
