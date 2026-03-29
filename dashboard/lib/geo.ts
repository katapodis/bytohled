// Statická mapa české geografie pro projekt BytoHled
// kraj → okres → města

export interface GeoData {
  [kraj: string]: {
    [okres: string]: string[]
  }
}

export const GEO: GeoData = {
  'Moravskoslezský kraj': {
    'Ostrava-město': ['Ostrava'],
    'Frýdek-Místek': [
      'Frýdek-Místek',
      'Čeladná',
      'Ostravice',
      'Frýdlant nad Ostravicí',
      'Pstruží',
      'Metylovice',
      'Kunčice pod Ondřejníkem',
      'Baška',
      'Staré Hamry',
    ],
  },
}

export function getCitiesForKraj(kraj: string): string[] {
  const okresy = GEO[kraj]
  if (!okresy) return []
  return Object.values(okresy).flat()
}

export function getCitiesForOkres(kraj: string, okres: string): string[] {
  return GEO[kraj]?.[okres] ?? []
}

export function getOkresyForKraj(kraj: string): string[] {
  return Object.keys(GEO[kraj] ?? {})
}

export function getKrajeWithCities(availableCities: string[]): string[] {
  return Object.keys(GEO).filter((kraj) =>
    getCitiesForKraj(kraj).some((c) => availableCities.includes(c))
  )
}

export function getOkresyWithCities(kraj: string, availableCities: string[]): string[] {
  return getOkresyForKraj(kraj).filter((okres) =>
    getCitiesForOkres(kraj, okres).some((c) => availableCities.includes(c))
  )
}

export function findKrajForCity(city: string): string | null {
  for (const [kraj, okresy] of Object.entries(GEO)) {
    for (const cities of Object.values(okresy)) {
      if (cities.includes(city)) return kraj
    }
  }
  return null
}

export function findOkresForCity(city: string): string | null {
  for (const okresy of Object.values(GEO)) {
    for (const [okres, cities] of Object.entries(okresy)) {
      if (cities.includes(city)) return okres
    }
  }
  return null
}
