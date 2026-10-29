/** Round axis steps (1, 2 or 5 times a power of ten) covering `max` in about four steps. */
export function niceTicks(max: number): number[] {
  if (max <= 0) return [0]
  const rough = max / 4
  const power = 10 ** Math.floor(Math.log10(rough))
  const step = ([1, 2, 5, 10].find((factor) => factor * power >= rough) ?? 10) * power
  const ticks = [0]
  while (ticks[ticks.length - 1]! < max) ticks.push(ticks[ticks.length - 1]! + step)
  return ticks
}
