import { z } from "zod";

export const ProfileResponseSchema = z.object({
  user: z.object({
    id: z.string().uuid(),
    email: z.string().email(),
    display_name: z.string(),
    avatar_url: z.string().nullable(),
    is_active: z.boolean(),
    is_onboarded: z.boolean(),
    last_login_at: z.string().datetime().nullable(),
  }),
  profile: z.object({
    bio: z.string().nullable(),
    website: z.string().nullable(),
    location: z.string().nullable(),
    preferences: z.record(z.string(), z.unknown()),
  }),
});

export const ProfileUpdateSchema = z.object({
  bio: z.string().optional(),
  website: z.string().url().optional().nullable(),
  location: z.string().optional(),
  display_name: z.string().min(1).max(100).optional(),
  preferences: z.record(z.string(), z.unknown()).optional(),
});

export const OnboardingRequestSchema = z.object({
  github_connected: z.boolean(),
  linkedin_connected: z.boolean(),
  knowledge_seeded: z.boolean(),
  first_draft_generated: z.boolean(),
  first_post_scheduled: z.boolean(),
});

export type ProfileResponse = z.infer<typeof ProfileResponseSchema>;
export type ProfileUpdate = z.infer<typeof ProfileUpdateSchema>;
export type OnboardingRequest = z.infer<typeof OnboardingRequestSchema>;