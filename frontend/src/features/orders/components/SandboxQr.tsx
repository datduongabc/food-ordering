// A fixed pattern with the three finder squares, so it reads as a QR code without encoding
// anything: the sandbox has no real MoMo transaction to point at.
function cells(): { x: number; y: number }[] {
  const result: { x: number; y: number }[] = []
  const finder = (ox: number, oy: number) => {
    for (let y = 0; y < 7; y++) {
      for (let x = 0; x < 7; x++) {
        const edge = x === 0 || y === 0 || x === 6 || y === 6
        const core = x >= 2 && x <= 4 && y >= 2 && y <= 4
        if (edge || core) result.push({ x: ox + x, y: oy + y })
      }
    }
  }
  finder(0, 0)
  finder(14, 0)
  finder(0, 14)
  let seed = 7
  for (let y = 0; y < 21; y++) {
    for (let x = 0; x < 21; x++) {
      const inFinder = (x < 8 && y < 8) || (x > 12 && y < 8) || (x < 8 && y > 12)
      seed = (seed * 1103515245 + 12345) % 2147483648
      if (!inFinder && seed % 3 === 0) result.push({ x, y })
    }
  }
  return result
}

const CELLS = cells()

export function SandboxQr({ label, className }: { label: string; className?: string }) {
  return (
    <svg role="img" aria-label={label} viewBox="0 0 21 21" className={className}>
      {CELLS.map(({ x, y }) => (
        <rect key={`${x}-${y}`} x={x} y={y} width="1" height="1" />
      ))}
    </svg>
  )
}
