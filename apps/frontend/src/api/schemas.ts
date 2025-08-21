import { z } from 'zod';

// Meta information for API responses
export const MetaSchema = z.object({
  total: z.number().optional(),
  page: z.number().optional(),
  pageSize: z.number().optional(),
  totalPages: z.number().optional(),
});

// Generic paginated response
export const PagedSchema = <T extends z.ZodTypeAny>(itemSchema: T) => z.object({
  data: z.array(itemSchema),
  meta: MetaSchema,
});

// Site/Facility schemas
export const SiteSchema = z.object({
  site_id: z.number(),
  site_code: z.string(),
  site_name: z.string(),
});

// Program schema
export const ProgramSchema = z.object({
  program_id: z.number(),
  program_name: z.string(),
});

// Subprogram schema  
export const SubprogramSchema = z.object({
  program_id: z.number(),
  subprogram_id: z.number(),
  subprogram_name: z.string(),
});

// Facility Summary schema
export const FacilitySummarySchema = z.object({
  total_sites: z.number(),
  total_programs: z.number(),
  total_beds: z.number(),
  avg_occupancy: z.number(),
  kpis: z.record(z.string(), z.any()).optional(),
});

// Patient schema
export const PatientSchema = z.object({
  patient_id: z.number(),
  age: z.number(),
  gender: z.enum(['Male', 'Female', 'Other']),
  home_lha: z.string(),
  facility_site_code: z.string(),
  admission_date: z.string().optional(),
});

// ED Encounter schema
export const EdEncounterSchema = z.object({
  encounter_id: z.number(),
  patient_id: z.number(),
  arrival_datetime: z.string(),
  ed_subservice: z.enum(['Adult ED', 'Pediatric ED', 'Urgent Care Centre']),
  acuity: z.enum(['CTAS_1', 'CTAS_2', 'CTAS_3', 'CTAS_4', 'CTAS_5']),
  disposition: z.enum(['Discharged', 'Admitted', 'Transferred', 'LWBS', 'Expired']),
});

// Projection Point schema
export const ProjectionPointSchema = z.object({
  year: z.number(),
  month: z.number().optional(),
  value: z.number(),
  metric: z.string(),
  site_code: z.string().optional(),
});

// Scenario-related schemas for the 3 screens
export const ScenarioParamsSchema = z.object({
  occupancy_target: z.number().min(0.8).max(1.0),
  los_delta: z.number().min(-0.5).max(0.5),
  alc_target: z.number().min(0.0).max(0.5),
  growth_pct: z.number().min(-0.2).max(0.2),
  schedule_code: z.string().default('Sched-A'),
  seasonality: z.boolean().default(false),
});

export const ScenarioRequestSchema = z.object({
  sites: z.array(z.number()).min(1),
  program_id: z.number(),
  baseline_year: z.number().default(2022),
  horizon_years: z.number().default(3),
  params: ScenarioParamsSchema,
});

export const SiteResultSchema = z.object({
  site_id: z.number(),
  site_code: z.string(),
  site_name: z.string(),
  admissions_projected: z.number(),
  los_effective: z.number(),
  patient_days: z.number(),
  census_average: z.number(),
  required_beds: z.number(),
  staffed_beds: z.number(),
  capacity_gap: z.number(),
  nursing_fte: z.number().nullable().optional(),
});

export const ScenarioKPIsSchema = z.object({
  total_required_beds: z.number(),
  total_staffed_beds: z.number(),
  total_capacity_gap: z.number(),
  total_nursing_fte: z.number().nullable().optional(),
  avg_occupancy: z.number(),
  total_admissions: z.number(),
  avg_los_effective: z.number(),
});

export const ScenarioResponseSchema = z.object({
  kpis: ScenarioKPIsSchema,
  by_site: z.array(SiteResultSchema),
  metadata: z.record(z.string(), z.any()).default({}),
});

// API Response wrappers
export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) => z.object({
  data: dataSchema,
  meta: z.record(z.string(), z.any()).default({}),
});