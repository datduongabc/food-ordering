import { z } from 'zod'

export const userSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string(),
  phone: z.string(),
  role: z.enum(['CUSTOMER', 'ADMIN']),
  is_email_verified: z.boolean(),
  created_at: z.string(),
})

export type User = z.infer<typeof userSchema>
