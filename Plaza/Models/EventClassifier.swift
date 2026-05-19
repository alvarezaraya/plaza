// EventClassifier.swift
// Clasifica eventos y genera resúmenes en español usando Apple Intelligence (FoundationModels).

import Foundation
import FoundationModels

@Generable(description: "Category for a cultural event")
enum EventTag {
    case musica
    case humor
    case teatro
    case deporte
    case familiar
    case otros

    var category: Event.Category {
        switch self {
        case .musica: .musica
        case .humor: .humor
        case .teatro: .teatro
        case .deporte: .deporte
        case .familiar: .familiar
        case .otros: .otros
        }
    }
}

@Generable(description: "Summary about a cultural event and its artist or performer")
struct EventSummary {
    @Guide(description: "Brief bio of the artist, band, or performer in Spanish (2-3 sentences). Use your knowledge if available.")
    var bio: String

    @Guide(description: "What attendees can expect at this event in Spanish (1-2 sentences)")
    var preview: String
}

enum EventClassifier {
    private static let classifyInstructions = """
        Classify the cultural event into exactly one category based on its title and description.
        - musica: concerts, music festivals, recitals, DJs, live music, bands, singers, tours
        - humor: stand-up comedy, comedy shows, monologues, humorists, comedians
        - teatro: theater plays, musicals, opera, ballet, dance performances, drama
        - deporte: boxing, MMA, soccer, running, marathons, wrestling, sports events
        - familiar: circus, children's shows, magic shows, puppets, family events
        - otros: events that don't clearly fit any category above
        """

    private static let summaryInstructions = """
        Genera un resumen breve e informativo sobre un evento cultural y su artista. \
        Usa tu conocimiento sobre el artista si lo tienes. Sé conciso y factual. \
        Responde siempre en español.
        """

    static var isAvailable: Bool {
        SystemLanguageModel(useCase: .general).isAvailable
    }

    static func classify(title: String, description: String) async -> Event.Category? {
        let model = SystemLanguageModel(useCase: .general)
        guard model.isAvailable else { return nil }

        let session = LanguageModelSession(model: model, instructions: classifyInstructions)

        do {
            let response = try await session.respond(
                to: "Event: \(title). \(description)",
                generating: EventTag.self
            )
            return response.content.category
        } catch {
            return nil
        }
    }

    static func generateSummary(event: Event) async -> EventSummary? {
        let model = SystemLanguageModel(useCase: .general)
        guard model.isAvailable else { return nil }

        let session = LanguageModelSession(model: model, instructions: summaryInstructions)

        let prompt = """
            Artista/Evento: \(event.title). \
            \(event.subtitle). \
            Categoría: \(event.category.rawValue). \
            Venue: \(event.venue), \(event.ciudad). \
            Descripción: \(event.blurb)
            """

        do {
            let response = try await session.respond(to: prompt, generating: EventSummary.self)
            return response.content
        } catch {
            return nil
        }
    }
}
