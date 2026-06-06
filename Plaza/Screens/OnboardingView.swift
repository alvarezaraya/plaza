// OnboardingView.swift
// Bienvenida en dos pasos: presentación de funciones + solicitud de permisos
// de ubicación y notificaciones. Controlado por plaza_onboarding_done en UserDefaults.
//
// El héroe reproduce el ícono de la app (glifo dorado sobre degradado): granate en
// modo claro, azul marino en modo oscuro — los mismos degradados de AppIcon.icon/icon.json.

import SwiftUI
import CoreLocation

struct OnboardingView: View {
    @Environment(LocationManager.self) private var location
    @Environment(ReminderManager.self) private var reminders
    var onFinish: () -> Void

    @State private var page = 0

    var body: some View {
        VStack(spacing: 0) {
            TabView(selection: $page) {
                WelcomePage(onContinue: { withAnimation(.smooth) { page = 1 } })
                    .tag(0)
                PermissionsPage(onFinish: onFinish)
                    .tag(1)
            }
            .tabViewStyle(.page(indexDisplayMode: .never))

            PageDots(count: 2, index: page)
                .padding(.bottom, 14)
        }
        .background(Color.plBg.ignoresSafeArea())
    }
}

// MARK: - App Icon Hero

/// Reproduce el ícono de la app: glifo dorado sobre degradado de esquina redondeada.
/// Cambia con el modo del sistema (claro = granate, oscuro = azul marino), igual que el ícono real.
private struct AppIconHero: View {
    @Environment(\.colorScheme) private var scheme
    var size: CGFloat = 132

    // Degradados tomados de AppIcon.icon/icon.json (display-p3).
    private var top: Color {
        scheme == .dark
            ? Color(.displayP3, red: 0.1127, green: 0.1629, blue: 0.4437)
            : Color(.displayP3, red: 0.4744, green: 0.1961, blue: 0.2327)
    }
    private var bottom: Color {
        scheme == .dark
            ? Color(.displayP3, red: 0.0662, green: 0.1046, blue: 0.1763)
            : Color(.displayP3, red: 0.3387, green: 0.1216, blue: 0.1600)
    }

    var body: some View {
        let radius = size * 0.2237 // proporción de squircle de iOS

        RoundedRectangle(cornerRadius: radius, style: .continuous)
            .fill(
                LinearGradient(
                    colors: [top, bottom],
                    startPoint: .top,
                    endPoint: UnitPoint(x: 0.5, y: 0.85)
                )
            )
            .overlay {
                Image("PlazaGlyph")
                    .resizable()
                    .scaledToFit()
                    .padding(size * 0.08)
            }
            .overlay {
                // brillo superior sutil, como el ícono real
                RoundedRectangle(cornerRadius: radius, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            colors: [.white.opacity(0.22), .clear],
                            startPoint: .top,
                            endPoint: .center
                        ),
                        lineWidth: 1
                    )
            }
            .frame(width: size, height: size)
            .shadow(color: .black.opacity(scheme == .dark ? 0.5 : 0.22), radius: 22, y: 12)
            .accessibilityHidden(true)
    }
}

// MARK: - Welcome

private struct WelcomePage: View {
    var onContinue: () -> Void
    @State private var appeared = false

    var body: some View {
        VStack(spacing: 0) {
            Spacer(minLength: 24)

            AppIconHero()
                .scaleEffect(appeared ? 1 : 0.85)
                .opacity(appeared ? 1 : 0)
                .padding(.bottom, 24)

            Text("Bienvenido a")
                .font(.plSerifItalic(19))
                .foregroundStyle(Color.plMuted)

            Text("Plaza")
                .font(.plDisplay(52))
                .kerning(-2)
                .foregroundStyle(Color.plFg)

            Text("Tu guía de eventos culturales")
                .font(.plSans(15))
                .foregroundStyle(Color.plDim)
                .padding(.top, 2)

            Spacer(minLength: 32)

            VStack(spacing: 18) {
                FeatureRow(icon: "square.grid.2x2.fill", tint: .plCardLeft,
                           title: "Descubre eventos",
                           subtitle: "Conciertos, teatro, humor y más cerca de ti")
                FeatureRow(icon: "map.fill", tint: .plCardCenter,
                           title: "Explora en el mapa",
                           subtitle: "Encuentra venues y eventos por ubicación")
                FeatureRow(icon: "calendar.badge.plus", tint: .plCardRight,
                           title: "Arma tu agenda",
                           subtitle: "Guarda eventos y recibe recordatorios")
                FeatureRow(icon: "sparkles", tint: .plAccent,
                           title: "Resúmenes con IA",
                           subtitle: "Conoce al artista antes de ir al show")
            }
            .padding(.horizontal, 32)

            Spacer(minLength: 32)

            PrimaryButton(title: "Continuar", filled: .plAccent, fg: .white, action: onContinue)
                .padding(.horizontal, 32)
                .padding(.bottom, 20)
        }
        .onAppear {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.05)) {
                appeared = true
            }
        }
    }
}

// MARK: - Permissions

private struct PermissionsPage: View {
    @Environment(LocationManager.self) private var location
    @Environment(ReminderManager.self) private var reminders
    var onFinish: () -> Void

    private var locationGranted: Bool {
        location.authorizationStatus == .authorizedWhenInUse
            || location.authorizationStatus == .authorizedAlways
    }

    var body: some View {
        VStack(spacing: 0) {
            Spacer(minLength: 24)

            AppIconHero(size: 108)
                .padding(.bottom, 22)

            Text("Permisos")
                .font(.plDisplay(40))
                .kerning(-1.4)
                .foregroundStyle(Color.plFg)

            Text("Para sacarle el máximo provecho")
                .font(.plSerifItalic(17))
                .foregroundStyle(Color.plMuted)
                .padding(.top, 2)

            Spacer(minLength: 36)

            VStack(spacing: 0) {
                PermissionRow(
                    icon: "location.fill", tint: .blue,
                    title: "Ubicación",
                    subtitle: "Ver eventos cercanos y distancias",
                    isOn: locationGranted,
                    toggle: { if $0 { location.requestPermission() } }
                )

                Divider().padding(.leading, 64)

                PermissionRow(
                    icon: "bell.fill", tint: .orange,
                    title: "Notificaciones",
                    subtitle: "Recordatorios antes del evento",
                    isOn: reminders.isAuthorized,
                    toggle: { if $0 { Task { await reminders.requestPermission() } } }
                )
            }
            .background(Color.plSurface, in: .rect(cornerRadius: PlSpace.cardRadius))
            .overlay(
                RoundedRectangle(cornerRadius: PlSpace.cardRadius)
                    .strokeBorder(Color.plHair, lineWidth: 0.5)
            )
            .padding(.horizontal, 32)

            Text("Puedes cambiar esto cuando quieras en Ajustes.")
                .font(.plSans(12))
                .foregroundStyle(Color.plDim)
                .padding(.top, 14)
                .padding(.horizontal, 40)
                .multilineTextAlignment(.center)

            Spacer(minLength: 32)

            PrimaryButton(title: "Empezar", filled: .plFg, fg: .plBg, action: onFinish)
                .padding(.horizontal, 32)

            Button(action: onFinish) {
                Text("Ahora no")
                    .font(.plSans(15))
                    .foregroundStyle(Color.plMuted)
            }
            .padding(.top, 12)
            .padding(.bottom, 20)
        }
    }
}

// MARK: - Components

private struct PrimaryButton: View {
    let title: String
    let filled: Color
    let fg: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.plSans(17, weight: .semibold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(filled, in: .capsule)
                .foregroundStyle(fg)
                .shadow(color: filled.opacity(0.3), radius: 12, y: 6)
        }
    }
}

private struct PageDots: View {
    let count: Int
    let index: Int

    var body: some View {
        HStack(spacing: 7) {
            ForEach(0..<count, id: \.self) { i in
                Capsule()
                    .fill(i == index ? Color.plAccent : Color.plHair)
                    .frame(width: i == index ? 22 : 7, height: 7)
                    .animation(.spring(response: 0.35, dampingFraction: 0.7), value: index)
            }
        }
        .accessibilityHidden(true)
    }
}

private struct FeatureRow: View {
    let icon: String
    let tint: Color
    let title: String
    let subtitle: String

    var body: some View {
        HStack(spacing: 15) {
            Image(systemName: icon)
                .font(.system(size: 20, weight: .medium))
                .foregroundStyle(tint)
                .frame(width: 46, height: 46)
                .background(tint.opacity(0.14), in: .rect(cornerRadius: 12, style: .continuous))
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.plSans(16, weight: .semibold))
                    .foregroundStyle(Color.plFg)
                Text(subtitle)
                    .font(.plSans(13))
                    .foregroundStyle(Color.plMuted)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 0)
        }
        .accessibilityElement(children: .combine)
    }
}

private struct PermissionRow: View {
    let icon: String
    let tint: Color
    let title: String
    let subtitle: String
    let isOn: Bool
    let toggle: (Bool) -> Void

    var body: some View {
        Toggle(isOn: Binding(get: { isOn }, set: toggle)) {
            Label {
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.plSans(16, weight: .semibold))
                        .foregroundStyle(Color.plFg)
                    Text(subtitle)
                        .font(.plSans(13))
                        .foregroundStyle(Color.plMuted)
                }
            } icon: {
                Image(systemName: icon)
                    .font(.system(size: 17))
                    .foregroundStyle(.white)
                    .frame(width: 32, height: 32)
                    .background(tint, in: .rect(cornerRadius: 8, style: .continuous))
            }
        }
        .tint(Color.plAccent)
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
    }
}
