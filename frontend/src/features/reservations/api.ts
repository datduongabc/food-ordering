import { queryOptions, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { api } from '@/lib/api/client'
import {
  reservationPolicySchema,
  reservationSchema,
  type Reservation,
  type ReservationInput,
} from './schemas'

export const reservationQueries = {
  policy: () =>
    queryOptions({
      queryKey: ['reservations', 'policy'],
      queryFn: () => api.get('/reservations/policy', reservationPolicySchema),
      // "Today" moves at midnight; a minute is plenty fresh for choosing a date.
      staleTime: 60 * 1000,
    }),
  mine: () =>
    queryOptions({
      queryKey: ['reservations', 'mine'],
      queryFn: () => api.get('/reservations/mine', z.array(reservationSchema)),
    }),
}

export function useBookTable() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ReservationInput) => api.post('/reservations', reservationSchema, input),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: reservationQueries.mine().queryKey }),
  })
}

export function useCancelReservation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.post(`/reservations/${id}/cancel`, reservationSchema),
    onSuccess: (cancelled) =>
      queryClient.setQueryData(reservationQueries.mine().queryKey, (list?: Reservation[]) =>
        list?.map((item) => (item.id === cancelled.id ? cancelled : item)),
      ),
  })
}
