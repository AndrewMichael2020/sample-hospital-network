import { useQuery, useMutation, useQueryClient, type UseQueryOptions, type UseMutationOptions } from '@tanstack/react-query';
import { apiClientFunctions } from './client';
import type {
  FacilitySummary,
  Patient,
  Site,
  Program,
  Subprogram,
  ProjectionPoint,
  ScenarioResponse,
  ScenarioRequest,
  Paged,
  PatientFilters,
  EdProjectionParams,
  ApiError,
} from './types';

// Query Keys
export const queryKeys = {
  sites: ['sites'] as const,
  programs: ['programs'] as const,
  subprograms: (programId?: number) => ['subprograms', programId] as const,
  facilitiesSummary: ['facilities-summary'] as const,
  patients: (filters: PatientFilters) => ['patients', filters] as const,
  edProjections: (params: EdProjectionParams) => ['ed-projections', params] as const,
  staffedBeds: (schedule: string) => ['staffed-beds', schedule] as const,
  baselines: (year: number) => ['baselines', year] as const,
  seasonality: (year: number) => ['seasonality', year] as const,
  staffingFactors: ['staffing-factors'] as const,
};

// Reference data hooks
export function useSites(options?: UseQueryOptions<Site[], ApiError>) {
  return useQuery({
    queryKey: queryKeys.sites,
    queryFn: apiClientFunctions.getSites,
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

export function usePrograms(options?: UseQueryOptions<Program[], ApiError>) {
  return useQuery({
    queryKey: queryKeys.programs,
    queryFn: apiClientFunctions.getPrograms,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

export function useSubprograms(
  programId?: number,
  options?: UseQueryOptions<Subprogram[], ApiError>
) {
  return useQuery({
    queryKey: queryKeys.subprograms(programId),
    queryFn: () => apiClientFunctions.getSubprograms(programId),
    staleTime: 5 * 60 * 1000,
    enabled: programId !== undefined,
    ...options,
  });
}

// Core feature hooks
export function useFacilitiesSummary(options?: UseQueryOptions<FacilitySummary, ApiError>) {
  return useQuery({
    queryKey: queryKeys.facilitiesSummary,
    queryFn: apiClientFunctions.getFacilitiesSummary,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
}

export function usePatients(
  filters: PatientFilters = {},
  options?: UseQueryOptions<Paged<Patient>, ApiError>
) {
  return useQuery({
    queryKey: queryKeys.patients(filters),
    queryFn: () => apiClientFunctions.getPatients(filters),
    staleTime: 1 * 60 * 1000, // 1 minute
    ...options,
  });
}

export function useEdProjections(
  params: EdProjectionParams,
  options?: UseQueryOptions<ProjectionPoint[], ApiError>
) {
  return useQuery({
    queryKey: queryKeys.edProjections(params),
    queryFn: () => apiClientFunctions.getEdProjections(params),
    staleTime: 5 * 60 * 1000,
    enabled: !!params.year,
    ...options,
  });
}

// Additional reference data hooks
export function useStaffedBeds(
  schedule = 'Sched-A',
  options?: UseQueryOptions<any[], ApiError>
) {
  return useQuery({
    queryKey: queryKeys.staffedBeds(schedule),
    queryFn: () => apiClientFunctions.getStaffedBeds(schedule),
    staleTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
}

export function useBaselines(
  year = 2022,
  options?: UseQueryOptions<any[], ApiError>
) {
  return useQuery({
    queryKey: queryKeys.baselines(year),
    queryFn: () => apiClientFunctions.getBaselines(year),
    staleTime: 10 * 60 * 1000,
    ...options,
  });
}

export function useSeasonality(
  year = 2022,
  options?: UseQueryOptions<any[], ApiError>
) {
  return useQuery({
    queryKey: queryKeys.seasonality(year),
    queryFn: () => apiClientFunctions.getSeasonality(year),
    staleTime: 10 * 60 * 1000,
    ...options,
  });
}

export function useStaffingFactors(options?: UseQueryOptions<any[], ApiError>) {
  return useQuery({
    queryKey: queryKeys.staffingFactors,
    queryFn: apiClientFunctions.getStaffingFactors,
    staleTime: 10 * 60 * 1000,
    ...options,
  });
}

// Scenario calculation mutation
export function useCalculateScenario(
  options?: UseMutationOptions<ScenarioResponse, ApiError, ScenarioRequest>
) {
  return useMutation({
    mutationFn: apiClientFunctions.calculateScenario,
    onSuccess: (data) => {
      // You could cache the result here if needed
      console.log('Scenario calculated successfully:', data);
    },
    onError: (error) => {
      console.error('Scenario calculation failed:', error);
    },
    ...options,
  });
}

// Utility hook for query client
export function useApiClient() {
  return useQueryClient();
}