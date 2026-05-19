// MapView.swift
// Mapa interactivo con marcadores por venue y tarjetas emergentes con detalle de eventos.

import SwiftUI
import MapKit

struct MapView: View {
    @Environment(EventoService.self) private var servicio
    @Environment(LocationManager.self) private var location
    @State private var selectedVenue: String?
    @State private var venueGroups: [VenueGroup] = []
    @State private var camera: MapCameraPosition = .userLocation(fallback: .region(
        .init(center: .init(latitude: -23.6509, longitude: -70.3975),
              span: .init(latitudeDelta: 0.06, longitudeDelta: 0.06))
    ))

    private var selectedEvents: [Event] {
        guard let venue = selectedVenue else { return [] }
        return venueGroups.first { $0.id == venue }?.events ?? []
    }

    var body: some View {
        Map(position: $camera, selection: $selectedVenue) {
            UserAnnotation()
            ForEach(venueGroups) { group in
                Marker(
                    group.name,
                    systemImage: group.events.count > 1 ? "\(min(group.events.count, 50)).circle.fill" : "music.note",
                    coordinate: group.coordinate
                )
                .tint(Color.plAccent)
                .tag(group.id)
            }
        }
        .mapStyle(.standard(elevation: .flat))
        .mapControls {
            MapCompass()
            MapUserLocationButton()
        }
        .ignoresSafeArea()
        .safeAreaInset(edge: .bottom) {
            if !selectedEvents.isEmpty {
                eventCards
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.smooth, value: selectedVenue)
        .onAppear {
            location.requestPermission()
            recomputeGroups()
        }
        .onChange(of: servicio.events) { recomputeGroups() }
    }

    private func recomputeGroups() {
        let allEvents = servicio.events
        var dict: [String: VenueGroup] = [:]
        for event in allEvents {
            let key = event.venue.lowercased()
            if dict[key] == nil {
                dict[key] = VenueGroup(
                    name: event.venue,
                    coordinate: event.coordinate,
                    events: []
                )
            }
            dict[key]?.events.append(event)
        }
        venueGroups = Array(dict.values).sorted { $0.name < $1.name }
        if selectedVenue == nil {
            selectedVenue = venueGroups.first?.id
        }
    }

    private func selectVenue(for event: Event) {
        let venueID = event.venue.lowercased()
        withAnimation(.smooth) {
            selectedVenue = venueID
            camera = .region(.init(
                center: event.coordinate,
                span: .init(latitudeDelta: 0.02, longitudeDelta: 0.02)
            ))
        }
    }

    // MARK: - Tarjetas horizontales

    private var eventCards: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(selectedEvents) { event in
                    EventGlassCard(event: event)
                        .frame(width: 280)
                }
            }
            .padding(.horizontal, 14)
        }
        .padding(.vertical, 10)
    }
}

// MARK: - Modelos auxiliares

struct VenueGroup: Identifiable, Hashable {
    var id: String { name.lowercased() }
    var name: String
    var coordinate: CLLocationCoordinate2D
    var events: [Event]

    static func == (lhs: VenueGroup, rhs: VenueGroup) -> Bool { lhs.id == rhs.id }
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Tarjeta glass

struct EventGlassCard: View {
    @Environment(EventoService.self) private var servicio
    @Environment(LocationManager.self) private var location
    let event: Event
    @State private var showAddedToast = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                PlTag(text: event.venue, color: .plAccent)
                Spacer()
                if let precio = event.price {
                    PlTag(text: precio)
                }
            }
            Text(event.title)
                .font(.plDisplay(20))
                .kerning(-0.6)
            if !event.subtitle.isEmpty {
                Text(event.subtitle)
                    .font(.plSerifItalic(14))
                    .foregroundStyle(Color.plMuted)
            }
            HStack(spacing: 8) {
                PlTag(text: event.dateText)
                if let dist = location.distanceText(event.coordinate) {
                    PlTag(text: dist, color: .plAccent)
                }
            }

            HStack(spacing: 8) {
                if let url = event.url {
                    Link(destination: url) {
                        Text("Ver evento")
                            .font(.plSans(14, weight: .semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(Color.plFg, in: .capsule)
                            .foregroundStyle(Color.plBg)
                    }
                }
                Button {
                    let added = servicio.toggleSaved(event)
                    if added {
                        showAddedToast = true
                        Task {
                            try? await Task.sleep(for: .seconds(1.5))
                            showAddedToast = false
                        }
                    }
                } label: {
                    Image(systemName: servicio.isSaved(event) ? "calendar.badge.checkmark" : "calendar.badge.plus")
                        .font(.system(size: 16))
                        .frame(width: 40, height: 40)
                }
                .glassEffect(.regular, in: .circle)
            }
        }
        .padding(14)
        .glassEffect(.regular, in: .rect(cornerRadius: PlSpace.cardRadius))
        .overlay(alignment: .top) {
            if showAddedToast {
                AddedToast()
                    .transition(.move(edge: .top).combined(with: .opacity))
                    .padding(.top, -40)
            }
        }
        .animation(.smooth, value: showAddedToast)
        .accessibilityElement(children: .combine)
    }
}

#Preview {
    MapView()
        .environment(EventoService())
        .environment(LocationManager())
}
