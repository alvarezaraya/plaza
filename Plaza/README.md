# Plaza · Xcode Handoff

Handoff para construir la dirección **Plaza** como app nativa SwiftUI en iOS 26.

## 1 · Crear el proyecto

1. Xcode → **File → New → Project**
2. **iOS → App**
3. Product Name: `Plaza` · Interface: **SwiftUI** · Language: **Swift**
4. Minimum Deployment: **iOS 26.0** (requerido para Liquid Glass nativo y `Tab(role: .search)`)

## 2 · Estructura de carpetas (arrastra al Xcode Project Navigator)

```
Plaza/
├── PlazaApp.swift          ← entry point
├── App/
│   └── RootTabView.swift   ← Liquid Glass tab bar + search separado
├── Theme/
│   └── PlazaTheme.swift    ← colores, fuentes, espaciado
├── Models/
│   └── Event.swift         ← modelo + datos de muestra
└── Screens/
    ├── HomeView.swift      ← feed editorial
    ├── MapView.swift       ← mapa cercano
    ├── EventDetailView.swift
    └── AgendaView.swift
```

Los archivos correspondientes están en este folder.

## 3 · Fuentes custom

Descarga e incorpora al bundle:

- **Bricolage Grotesque** (variable) — Google Fonts
- **Instrument Serif** (regular + italic) — Google Fonts
- **JetBrains Mono** (medium) — para tags y coordenadas

Pasos:
1. Arrastra los `.ttf` al proyecto. Marca **Copy items** y el target Plaza.
2. En `Info.plist` agrega `Fonts provided by application` (UIAppFonts) listando cada archivo.
3. `PlazaTheme.swift` ya define los `Font` extensions; solo cambia el nombre PostScript si difiere.

## 4 · Liquid Glass — qué es nativo en iOS 26

No necesitas recrear el blur. El sistema ya lo hace:

| Mockup HTML hizo a mano | iOS 26 lo hace solo |
|---|---|
| `backdrop-filter: blur(32px) saturate(180%)` en pill | `TabView { ... }` por defecto |
| Pill con shine inset + tint translúcido | `.glassEffect()` o `.glassEffect(.regular.tint(...))` |
| Botón circular separado con lupa | `Tab(value:, role: .search) { ... }` ← se renderiza separado a la derecha |
| Tarjeta translúcida sobre mapa | `.glassEffect(.regular, in: .rect(cornerRadius: 14))` |

Ver `RootTabView.swift` para el patrón exacto.

## 5 · Tokens de diseño (resumen)

| Token | Valor |
|---|---|
| `bg` | `#fbf8f1` (bone) |
| `surface` | `#f3eee2` |
| `fg` | `#0e0c0a` (ink) |
| `muted` | `#5c544a` |
| `dim` | `#8e8675` |
| `hair` | `#d6cfbf` (bordes) |
| `accent` | `#c5832b` (ochre) |
| `accentDark` | `#9c6620` |

| Tipografía | Uso |
|---|---|
| Bricolage Grotesque 600, opsz 60 | display (h1, números grandes) |
| Bricolage Grotesque 400/500 | UI body, botones, tabs |
| Instrument Serif italic | quotes, decoraciones editoriales |
| JetBrains Mono 500, tracking 0.6 | tags, coordenadas, timestamps |

| Radios | |
|---|---|
| Tarjeta de evento | 14 |
| Pill / pill button | 99 (capsule) |
| Tab bar pill | 32 |
| Botón circular Cerca | 32 (radio = mitad de 64×64) |

## 6 · SF Symbols equivalentes

| Mockup | SF Symbol | Notas |
|---|---|---|
| Plaza (grid 2×2) | `square.grid.2x2` / `square.grid.2x2.fill` | |
| Cerca (lupa) | `magnifyingglass` | el sistema lo provee al usar `role: .search` |
| Agenda (calendario) | `calendar` | |
| Perfil (persona) | `person.crop.circle` / `.fill` | |
| Guardar | `bookmark` / `bookmark.fill` | |
| Recordatorio | `bell` / `bell.fill` | |
| Compartir | `square.and.arrow.up` | |
| Distancia | `location` | |

## 7 · Roadmap sugerido

1. ✅ Tokens (`PlazaTheme.swift`) → comprobar colores en Preview
2. ✅ `RootTabView` con 3 tabs + search role → debería verse el Liquid Glass real al correr
3. ✅ `HomeView` con feed estático (sample data)
4. `MapView` con `Map` de MapKit + `.glassEffect()` en la card flotante
5. `EventDetailView` — large title, sticky CTA bar
6. `AgendaView` — lista agrupada por fecha
7. Pulir tipografía + spacing comparando contra mockup HTML
8. Persistencia de favoritos (SwiftData o UserDefaults)
9. Notificaciones para recordatorios (UserNotifications)
10. CoreLocation para "eventos cerca de ti"

## 8 · Tips

- **Preview real del glass:** los efectos Liquid Glass solo se ven correctamente en simulador iOS 26 o device, no siempre en SwiftUI Previews. Compila y corre.
- **Dynamic Type:** usa `.font(.custom(..., relativeTo: .largeTitle))` para que escale.
- **Dark mode:** Plaza usa paleta clara; define variantes oscuras en `PlazaTheme.swift` cuando lo abordes.
- **Accesibilidad:** todos los botones glass requieren `.accessibilityLabel` (los SVG decorativos del mockup no son leídos por VoiceOver).
