// HomeView.swift
// Feed principal de eventos con filtro por categoría, tarjeta destacada y acciones de guardado.

import SwiftUI

struct HomeView: View {
    @Environment(EventoService.self) private var servicio
    @Environment(LocationManager.self) private var location
    @Environment(ComunaManager.self) private var comunaManager
    @State private var selectedCategory: Event.Category?
    @State private var eventToEdit: Event?
    @State private var showAddedToast = false
    @State private var showProfile = false
    @State private var showComunaPicker = false
    @State private var showFilter = false
    @AppStorage("plaza_max_distance_km") private var maxDistanceKm: Double = 0

    private var events: [Event] { servicio.events }

    private var filteredEvents: [Event] {
        var result = events
            .byComune(comunaManager.selectedComuna)
            .byMaxDistance(maxDistanceKm, from: location.userLocation)
        if let cat = selectedCategory {
            result = result.filter { $0.category == cat }
        }
        return result
    }

    var body: some View {
        NavigationStack {
            listContent
                .listStyle(.plain)
                .scrollContentBackground(.hidden)
                .background(Color.plBg)
                .toolbar(.hidden, for: .navigationBar)
                .navigationDestination(for: Event.self) { EventDetailView(event: $0) }
                .sheet(item: $eventToEdit) { EventEditView(event: $0) }
                .sheet(isPresented: $showProfile) { ProfileView() }
                .sheet(isPresented: $showComunaPicker) { ComunaPickerView() }
                .sheet(isPresented: $showFilter) {
                    FilterSheetView(selectedCategory: $selectedCategory, maxDistanceKm: $maxDistanceKm)
                }
                .refreshable { servicio.cargarEventos() }
                .overlay(alignment: .top) {
                    if showAddedToast {
                        AddedToast()
                            .transition(.move(edge: .top).combined(with: .opacity))
                            .padding(.top, 60)
                    }
                }
                .animation(.smooth, value: showAddedToast)
        }
        .onAppear {
            if events.isEmpty { servicio.cargarEventos() }
            location.requestPermission()
            if let loc = location.userLocation {
                comunaManager.autoDetectar(desde: loc)
            }
        }
        .onChange(of: location.userLocation) { _, newLoc in
            if let loc = newLoc { comunaManager.autoDetectar(desde: loc) }
        }
    }

    private var listContent: some View {
        List {
            headerBlock
                .plainRow()

            if servicio.cargando {
                ProgressView()
                    .frame(maxWidth: .infinity)
                    .padding(.top, 60)
                    .plainRow()
            } else if let error = servicio.error {
                ContentUnavailableView {
                    Label("Sin conexión", systemImage: "wifi.slash")
                } description: {
                    Text(error)
                } actions: {
                    Button("Reintentar") { servicio.cargarEventos() }
                        .buttonStyle(.borderedProminent)
                        .tint(Color.plAccent)
                }
                .plainRow()
            } else {
                if filteredEvents.isEmpty {
                    ContentUnavailableView(
                        "Sin eventos",
                        systemImage: "calendar.badge.exclamationmark",
                        description: Text("No hay eventos en esta categoría")
                    )
                    .plainRow()
                } else {
                    if let featured = filteredEvents.first {
                        NavigationLink(value: featured) {
                            FeatureCard(event: featured)
                        }
                        .buttonStyle(.plain)
                        .listRowInsets(EdgeInsets(top: 18, leading: PlSpace.gutter, bottom: 18, trailing: PlSpace.gutter))
                        .listRowSeparator(.hidden)
                        .listRowBackground(Color.plBg)
                    }

                    ForEach(filteredEvents.dropFirst()) { event in
                        NavigationLink(value: event) {
                            EventRowContent(event: event)
                        }
                        .swipeActions(edge: .trailing) {
                            Button { eventToEdit = event } label: {
                                Label("Editar", systemImage: "pencil")
                            }
                            .tint(Color.plAccent)
                        }
                        .swipeActions(edge: .leading) {
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
                                Label(
                                    servicio.isSaved(event) ? "Quitar" : "Agenda",
                                    systemImage: servicio.isSaved(event) ? "calendar.badge.minus" : "calendar.badge.plus"
                                )
                            }
                            .tint(servicio.isSaved(event) ? .red : .green)
                        }
                        .listRowInsets(EdgeInsets(top: 0, leading: PlSpace.gutter, bottom: 0, trailing: PlSpace.gutter))
                        .listRowBackground(Color.plBg)
                    }
                }
            }
        }
    }

    private var hasActiveFilters: Bool {
        selectedCategory != nil || maxDistanceKm > 0
    }

    // MARK: - Header

    private var headerBlock: some View {
        ZStack {
            // Píldora de ubicación centrada
            Button {
                showComunaPicker = true
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: comunaManager.isDetecting ? "location.slash" : "location.fill")
                        .font(.system(size: 11))
                    Text(comunaManager.selectedComuna)
                        .font(.plSans(13, weight: .semibold))
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.plSurface, in: .capsule)
                .foregroundStyle(Color.plFg)
            }
            .accessibilityLabel("Ubicación: \(comunaManager.selectedComuna). Toca para cambiar.")

            // Botones derecha dentro de un contenedor Liquid Glass
            HStack {
                Spacer()
                HStack(spacing: 0) {
                    Button {
                        showFilter = true
                    } label: {
                        Image(systemName: "slider.horizontal.3")
                            .font(.system(size: 14, weight: .medium))
                            .frame(width: 40, height: 36)
                            .foregroundStyle(hasActiveFilters ? Color.plAccent : Color.plFg)
                            .overlay(alignment: .topTrailing) {
                                if hasActiveFilters {
                                    Circle()
                                        .fill(Color.plAccent)
                                        .frame(width: 6, height: 6)
                                        .offset(x: -6, y: 6)
                                }
                            }
                    }
                    .accessibilityLabel("Filtros\(hasActiveFilters ? " (activos)" : "")")

                    Rectangle()
                        .fill(Color.primary.opacity(0.12))
                        .frame(width: 0.5, height: 18)

                    Button {
                        showProfile = true
                    } label: {
                        Image(systemName: "person.crop.circle")
                            .font(.system(size: 17))
                            .frame(width: 40, height: 36)
                            .foregroundStyle(Color.plFg)
                    }
                    .accessibilityLabel("Perfil")
                }
                .glassEffect(.regular, in: .capsule)
                .overlay(Capsule().strokeBorder(Color.primary.opacity(0.1), lineWidth: 0.5))
            }
        }
        .padding(.top, 8)
        .padding(.horizontal, PlSpace.gutter)
    }
}

// MARK: - List row modifier

extension View {
    func plainRow() -> some View {
        self
            .listRowSeparator(.hidden)
            .listRowInsets(EdgeInsets())
            .listRowBackground(Color.plBg)
    }
}

// MARK: - Feature Card

struct FeatureCard: View {
    let event: Event
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            AsyncImage(url: event.imageURL) { phase in
                if let img = phase.image {
                    img.resizable().scaledToFill()
                } else {
                    Rectangle().fill(Color.plSurface)
                }
            }
            .aspectRatio(4/3, contentMode: .fit)
            .clipShape(.rect(cornerRadius: PlSpace.cardRadius))

            HStack {
                PlTag(text: event.dateText)
                Spacer()
                PlTag(text: event.venue)
            }

            Text(event.title)
                .font(.plDisplay(28))
                .kerning(-0.8)
                .foregroundStyle(Color.plFg)

            if !event.subtitle.isEmpty {
                Text(event.subtitle)
                    .font(.plSerifItalic(18))
                    .foregroundStyle(Color.plMuted)
            }

            HStack(spacing: 8) {
                PlTag(text: event.price ?? "Gratis", color: .plAccent)
                if !event.otherDates.isEmpty {
                    PlTag(text: "+\(event.otherDates.count) fechas", color: .plAccent)
                }
            }
        }
        .accessibilityElement(children: .combine)
    }
}

// MARK: - Event Row

struct EventRowContent: View {
    @Environment(LocationManager.self) private var location
    let event: Event

    var body: some View {
        HStack(alignment: .top, spacing: 14) {
            Image(systemName: event.category.icon)
                .font(.system(size: 22))
                .foregroundStyle(Color.plAccent)
                .frame(width: 54, height: 54)
                .background(Color.plSurface, in: .rect(cornerRadius: 10))

            VStack(alignment: .leading, spacing: 4) {
                Text(event.title)
                    .font(.plSans(17, weight: .medium))
                    .foregroundStyle(Color.plFg)
                    .lineLimit(2)
                if !event.subtitle.isEmpty {
                    Text(event.subtitle)
                        .font(.plSerifItalic(14))
                        .foregroundStyle(Color.plMuted)
                        .lineLimit(1)
                }
                HStack(spacing: 8) {
                    PlTag(text: event.dateText)
                    PlTag(text: event.venue)
                    if let dist = location.distanceText(event.coordinate) {
                        PlTag(text: dist, color: .plAccent)
                    }
                }
                .padding(.top, 2)
                HStack(spacing: 8) {
                    PlTag(text: event.price ?? "gratis")
                    if !event.otherDates.isEmpty {
                        PlTag(text: "+\(event.otherDates.count) fechas", color: .plAccent)
                    }
                }
            }
            Spacer(minLength: 0)
        }
        .padding(.vertical, 14)
        .accessibilityElement(children: .combine)
    }
}

// MARK: - Category Chip

struct CategoryChip: View {
    let label: String
    let icon: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon).font(.system(size: 12))
                Text(label).font(.plSans(13, weight: .medium))
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(isSelected ? Color.plFg : Color.plSurface, in: .capsule)
            .foregroundStyle(isSelected ? Color.plBg : Color.plMuted)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(label)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
    }
}

// MARK: - Comuna Picker

struct ComunaPickerView: View {
    @Environment(ComunaManager.self) private var comunaManager
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Button {
                        comunaManager.resetearAAutoDeteccion()
                        dismiss()
                    } label: {
                        Label("Detectar automáticamente", systemImage: "location.circle")
                            .foregroundStyle(Color.plAccent)
                    }
                }

                ForEach(ComunaManager.regiones) { region in
                    Section(region.id) {
                        ForEach(region.comunas, id: \.self) { comuna in
                            Button {
                                comunaManager.seleccionar(comuna)
                                dismiss()
                            } label: {
                                HStack {
                                    Text(comuna)
                                        .foregroundStyle(Color.plFg)
                                    Spacer()
                                    if comunaManager.selectedComuna == comuna {
                                        Image(systemName: "checkmark")
                                            .foregroundStyle(Color.plAccent)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Ubicación")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Listo") { dismiss() }
                }
            }
        }
    }
}

// MARK: - Filter Sheet

struct FilterSheetView: View {
    @Binding var selectedCategory: Event.Category?
    @Binding var maxDistanceKm: Double
    @Environment(\.dismiss) private var dismiss

    private static let distanceOptions: [(String, Double)] = [
        ("Sin límite", 0), ("10 km", 10), ("25 km", 25), ("50 km", 50), ("100 km", 100),
    ]

    private var hasFilters: Bool { selectedCategory != nil || maxDistanceKm > 0 }

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 28) {
                filterSection("Categoría") {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            CategoryChip(label: "Todos", icon: "square.grid.2x2", isSelected: selectedCategory == nil) {
                                withAnimation { selectedCategory = nil }
                            }
                            ForEach(Event.Category.allCases, id: \.self) { cat in
                                CategoryChip(label: cat.rawValue, icon: cat.icon, isSelected: selectedCategory == cat) {
                                    withAnimation { selectedCategory = cat }
                                }
                            }
                        }
                        .padding(.horizontal, PlSpace.gutter)
                        .padding(.vertical, 4)
                    }
                }

                filterSection("Distancia máxima") {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(Self.distanceOptions, id: \.1) { label, km in
                                CategoryChip(
                                    label: label,
                                    icon: km == 0 ? "xmark.circle" : "location",
                                    isSelected: maxDistanceKm == km
                                ) {
                                    withAnimation { maxDistanceKm = km }
                                }
                            }
                        }
                        .padding(.horizontal, PlSpace.gutter)
                        .padding(.vertical, 4)
                    }
                }

                Spacer()
            }
            .padding(.top, 20)
            .background(Color.plBg)
            .navigationTitle("Filtros")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Listo") { dismiss() }
                }
                if hasFilters {
                    ToolbarItem(placement: .topBarLeading) {
                        Button("Limpiar") {
                            withAnimation { selectedCategory = nil; maxDistanceKm = 0 }
                        }
                        .foregroundStyle(Color.plAccent)
                    }
                }
            }
        }
        .presentationDetents([.medium])
    }

    private func filterSection<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.plSans(13, weight: .semibold))
                .foregroundStyle(Color.plMuted)
                .padding(.horizontal, PlSpace.gutter)
            content()
        }
    }
}

#Preview {
    HomeView()
        .environment(EventoService())
        .environment(LocationManager())
        .tint(.plAccent)
}
