import { z } from 'zod';
import {
  MetaSchema,
  SiteSchema,
  ProgramSchema,
  SubprogramSchema,
  FacilitySummarySchema,
  PatientSchema,
  EdEncounterSchema,
  ProjectionPointSchema,
  ScenarioParamsSchema,
  ScenarioRequestSchema,
  SiteResultSchema,
  ScenarioKPIsSchema,
  ScenarioResponseSchema,
} from './schemas';

// Basic types
export type Meta = z.infer<typeof MetaSchema>;
export type Paged<T> = { data: T[]; meta: Meta };

// Domain types
export type Site = z.infer<typeof SiteSchema>;
export type Program = z.infer<typeof ProgramSchema>;
export type Subprogram = z.infer<typeof SubprogramSchema>;
export type FacilitySummary = z.infer<typeof FacilitySummarySchema>;
export type Patient = z.infer<typeof PatientSchema>;
export type EdEncounter = z.infer<typeof EdEncounterSchema>;
export type ProjectionPoint = z.infer<typeof ProjectionPointSchema>;

// Scenario types
export type ScenarioParams = z.infer<typeof ScenarioParamsSchema>;
export type ScenarioRequest = z.infer<typeof ScenarioRequestSchema>;
export type SiteResult = z.infer<typeof SiteResultSchema>;
export type ScenarioKPIs = z.infer<typeof ScenarioKPIsSchema>;
export type ScenarioResponse = z.infer<typeof ScenarioResponseSchema>;

// API parameter types
export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

export interface PatientFilters extends PaginationParams {
  q?: string;
}

export interface EdProjectionParams {
  year: number;
  method?: string;
}

// Error types
export interface ApiError {
  error: string;
  details?: Array<{
    type: string;
    message: string;
    field?: string;
  }>;
  request_id?: string;
}

// Scenario preset types for Screen 1
export type ScenarioPreset = 'baseline' | 'target' | 'stress' | 'best';

export interface ScenarioBuilderForm {
  name: string;
  preset: ScenarioPreset;
  baseline_year: number;
  horizon_years: number;
  selected_sites: number[];
  program_id: number;
  selected_programs?: number[];
  params: ScenarioParams;
  overrides?: {
    program_id: number;
    subprogram_id?: number;
    growth_override?: number;
    los_override?: number;
    alc_override?: number;
  };
}

// Screen comparison types
export interface ScenarioComparison {
  scenario_a: ScenarioResponse & { name: string };
  scenario_b: ScenarioResponse & { name: string };
  deltas: {
    kpi_deltas: Partial<ScenarioKPIs>;
    site_deltas: Array<SiteResult & { delta_gap: number }>;
  };
}