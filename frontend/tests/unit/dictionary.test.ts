import { describe, expect, it } from 'vitest'
import { en } from '@/i18n/en'
import { vi } from '@/i18n/vi'

function keyPaths(value: unknown, prefix = ''): string[] {
  if (typeof value !== 'object' || value === null) return [prefix]
  return Object.entries(value).flatMap(([key, child]) =>
    keyPaths(child, prefix ? `${prefix}.${key}` : key),
  )
}

function placeholders(text: string): string[] {
  return [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1] ?? '').sort()
}

describe('dictionaries', () => {
  // Record-typed sections (errors, categories, statuses) escape the type checker's key check.
  it('have exactly the same keys in both languages', () => {
    expect(keyPaths(en).sort()).toEqual(keyPaths(vi).sort())
  })

  it('use the same placeholders in both languages', () => {
    const lookup = (dict: unknown, path: string) =>
      path.split('.').reduce<unknown>((node, key) => (node as Record<string, unknown>)[key], dict)
    for (const path of keyPaths(vi)) {
      const viText = lookup(vi, path)
      if (typeof viText !== 'string') continue
      expect(placeholders(lookup(en, path) as string), path).toEqual(placeholders(viText))
    }
  })

  it('never use the em dash', () => {
    expect(JSON.stringify([vi, en])).not.toContain('—')
  })
})
